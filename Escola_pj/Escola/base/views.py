from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.hashers import make_password
from django.contrib import messages
from django.utils import timezone
from django.urls import reverse
from .models import *

# Helpers for role checks
def is_superintendente(user): return user.is_authenticated and user.role == 'superintendente'
def is_secretario(user): return user.is_authenticated and user.role == 'secretario'
def is_professor(user): return user.is_authenticated and user.role == 'professor'
def is_actor(user): return user.is_authenticated and user.role in ['professor', 'secretario', 'superintendente']
def is_secretario_or_superintendente(user): return user.is_authenticated and user.role in ['secretario', 'superintendente']



@login_required
def dashboard(request):
    ## if request.method == 'POST':
    if request.user.role == 'superintendente':
        classes = Classe.objects.all()
        usuarios_disponiveis = Usuario.objects.filter(role='professor', professor__isnull=True)
        # return render(request, 'tela_inicial/layout_base.html', {'perfil': 'Superintendente', 'classes': classes, 'usuarios_disponiveis': usuarios_disponiveis})
        return render(request, 'tela_inicial/dashboard_superintendente.html', {'perfil': 'Superintendente', 'classes': classes, 'usuarios_disponiveis': usuarios_disponiveis})
    elif request.user.role == 'secretario':
        return render(request, 'tela_inicial/dashboard_secretario.html', {'perfil': 'Secretário'})
    elif request.user.role == 'professor':
        return render(request, 'tela_inicial/dashboard_professor.html', {'perfil': 'Professor'})
    return redirect('login')

# --- Superintendente ---
@user_passes_test(is_superintendente)
# def usuario_add(request):
#     return render(request, 'usuario_form.html')



@user_passes_test(is_superintendente)
def cadastrar_professor(request):
    classes = Classe.objects.all()
    # Usuários existentes que ainda não são professores
    usuarios_disponiveis = Usuario.objects.filter(role='professor', professor__isnull=True)
    if request.method == 'POST':
        usuario_id = request.POST.get('usuario')
        classe_id = request.POST.get('classe')
        tipo_usuario = request.POST.get('tipo_usuario') or 'professor'
        username = request.POST.get('username')
        email = request.POST.get('email')
        # compatibilidade com templates que usam 'senha'
        password = request.POST.get('password') or request.POST.get('senha')

        # Se for professor, valida se selecionou uma classe
        classe = None
        if tipo_usuario == 'professor':
            if not classe_id:
                messages.error(request, "Selecione uma classe para professor.")
                return redirect('cadastrar_professor')
            classe = get_object_or_404(Classe, id=classe_id)

        usuario = None
        if usuario_id:
            # Associar usuário existente
            usuario = get_object_or_404(Usuario, id=usuario_id)
            # garantir role conforme tipo selecionado
            if tipo_usuario and usuario.role != tipo_usuario:
                usuario.role = tipo_usuario
                usuario.save()
        elif username and password:
            # Criar novo usuário usando create_user para lidar com hashing
            try:
                usuario = Usuario.objects.create_user(username=username, email=email, password=password)
                # definir role conforme seleção (default professor)
                usuario.role = tipo_usuario or 'professor'
                usuario.save()
            except Exception as e:
                messages.error(request, f"Erro ao criar usuário: {e}")
                return redirect('cadastrar_professor')
        else:
            messages.error(request, "Selecione um usuário existente ou preencha os dados para criar um novo usuário.")
            return redirect('cadastrar_professor')
        # Se for professor, cria perfil de Professor (verifica existência)
        if tipo_usuario == 'professor':
            if hasattr(usuario, 'professor'):
                messages.error(request, "Este usuário já possui perfil de professor.")
                return redirect('cadastrar_professor')
            try:
                Professor.objects.create(usuario=usuario, classe=classe)
                messages.success(request, f"Professor {usuario.username} cadastrado com sucesso!")
            except Exception as e:
                messages.error(request, f"Erro ao cadastrar professor: {e}")
                return redirect('cadastrar_professor')
        else:
            # Para secretário, apenas confirma criação/atualização de role
            messages.success(request, f"Usuário {usuario.username} cadastrado/atualizado como {usuario.role}.")

        return redirect('dashboard')

    return render(request, 'tela_inicial/dashboard_superintendente.html', {'classes': classes, 'usuarios_disponiveis': usuarios_disponiveis})

 
@user_passes_test(is_superintendente)
def classe_list(request):
    classes = Classe.objects.all()
    return render(request, 'classe_list.html', {'classes': classes})

@user_passes_test(is_superintendente)
def periodo_list(request):
    # Mostrar períodos da igreja do usuário quando disponível; caso contrário, mostrar todos
    user_igreja = getattr(request.user, 'igreja', None)
    if user_igreja:
        periodos = Trimestre.objects.filter(igreja=user_igreja).order_by('-ano', 'trimestre')
    else:
        periodos = Trimestre.objects.all()
    return render(request, 'periodo_list.html', {'periodos': periodos})

@user_passes_test(is_superintendente)
def periodo_iniciar(request):
    user_igreja = getattr(request.user, 'igreja', None)
    if request.method == 'POST':
        nome = request.POST.get('nome')
        ano = request.POST.get('ano') or timezone.now().year
        igreja_id = request.POST.get('igreja') or (user_igreja.id if user_igreja else None)
        if not igreja_id:
            messages.error(request, 'Selecione uma igreja.')
            return redirect('periodo_iniciar')
        igreja = get_object_or_404(Igreja, id=igreja_id)
        # Validar escolha de trimestre (permitir 1º a 4º)
        allowed = ['1', '2', '3', '4', '1º Trimestre', '2º Trimestre', '3º Trimestre', '4º Trimestre']
        if nome not in allowed:
            messages.error(request, 'Selecione um trimestre válido (1-4).')
            return redirect('periodo_iniciar')

        # Normalizar nome para formato '1º Trimestre', etc.
        mapping = {'1': '1º Trimestre', '2': '2º Trimestre', '3': '3º Trimestre', '4': '4º Trimestre'}
        nome_normalizado = mapping.get(nome, nome)

        # Verificar duplicidade (igreja, trimestre, ano)
        if Trimestre.objects.filter(igreja=igreja, trimestre=nome_normalizado, ano=ano).exists():
            messages.error(request, f'O trimestre {nome_normalizado}/{ano} já existe para a igreja {igreja.nome}.')
            return redirect('periodo_iniciar')

        # Desativa outros trimestres ativos somente para a igreja selecionada
        Trimestre.objects.filter(igreja=igreja, ativo=True).update(ativo=False)
        trimestre = Trimestre.objects.create(igreja=igreja, trimestre=nome_normalizado, ano=ano, ativo=True, concluido=False)
        
        # Redirecionar para criar aulas do trimestre (CDU.007)
        messages.success(request, f"Trimestre {nome_normalizado}/{ano} iniciado. Agora crie as aulas do trimestre.")
        return redirect('periodo_criar_aulas', trimestre_id=trimestre.id)

    igrejas = Igreja.objects.all()
    return render(request, 'periodo_iniciar.html', {'igrejas': igrejas, 'user_igreja': user_igreja})

@user_passes_test(is_superintendente)
def periodo_concluir(request, id=None):
    # Suporta POST com 'periodo_id' ou chamada via URL com id
    if request.method != 'POST':
        return redirect('periodo_list')

    periodo_id = request.POST.get('periodo_id') or id
    if not periodo_id:
        messages.error(request, 'Nenhum trimestre selecionado para concluir.')
        return redirect('periodo_list')

    periodo = get_object_or_404(Trimestre, id=periodo_id)
    periodo.concluido = True
    periodo.ativo = False
    periodo.save()
    # Marca todas as aulas deste trimestre como concluídas (CDU.008)
    try:
        Aula.objects.filter(trimestre=periodo).update(concluida=True)
    except Exception:
        pass
    messages.success(request, "Trimestre concluído.")
    return redirect('periodo_list')


@user_passes_test(is_superintendente)
def classe_create(request, id=None):
    """Cria uma nova Classe ou edita o nome de uma existente.

    Se `id` for fornecido e o método for POST, atualiza o registro.
    Caso contrário, cria uma nova Classe. Igreja é obrigatória.
    """
    if request.method != 'POST':
        return redirect('classe_list')

    nome = request.POST.get('nome', '').strip()
    if not nome:
        messages.error(request, 'Nome da classe é obrigatório.')
        return redirect('classe_list')
    
    # CDU.008: Bloquear criação/edição de classes se trimestre ativo foi concluído
    trimestre_ativo = Trimestre.objects.filter(ativo=True).first()
    if trimestre_ativo and trimestre_ativo.concluido:
        messages.error(request, 'Não é possível criar ou editar classes em um trimestre concluído.')
        return redirect('classe_list')

    try:
        if id:
            # Editar classe existente
            classe = get_object_or_404(Classe, id=id)
            classe.nome = nome
            classe.save()
            messages.success(request, f'Classe "{nome}" atualizada com sucesso.')
        else:
            # Criar nova classe
            # Obter Igreja do usuário logado ou usar a primeira disponível
            user_igreja = getattr(request.user, 'igreja', None)
            if not user_igreja:
                # Se o usuário não tem igreja, tenta usar a primeira da base
                user_igreja = Igreja.objects.first()
                if not user_igreja:
                    messages.error(request, 'Nenhuma Igreja disponível. Crie uma Igreja primeiro.')
                    return redirect('classe_list')
            
            Classe.objects.create(nome=nome, igreja=user_igreja)
            messages.success(request, f'Classe "{nome}" criada com sucesso.')
    except Exception as e:
        messages.error(request, f'Erro ao processar classe: {str(e)}')

    return redirect('classe_list')

# --- Secretário ---
@user_passes_test(is_actor)
def aluno_matricular(request, classe_id=None):
    # Actor must choose a class (or provide classe_id)
    if classe_id is None:
        # Se for professor, mostrar só sua classe
        if request.user.role == 'professor':
            try:
                professor = Professor.objects.get(usuario=request.user)
                return redirect('aluno_matricular_classe', classe_id=professor.classe.id)
            except Professor.DoesNotExist:
                messages.error(request, 'Você não está vinculado a nenhuma classe.')
                return redirect('dashboard')
        else:
            classes = Classe.objects.all()
            return render(request, 'aluno_matricula_select_classe.html', {'classes': classes})

    classe = get_object_or_404(Classe, id=classe_id)
    
    # Verificação: professor só pode matricular na sua classe
    if request.user.role == 'professor':
        try:
            professor = Professor.objects.get(usuario=request.user)
            if professor.classe.id != classe.id:
                messages.error(request, 'Você só pode matricular alunos da sua classe.')
                return redirect('dashboard')
        except Professor.DoesNotExist:
            messages.error(request, 'Você não está vinculado a nenhuma classe.')
            return redirect('dashboard')
    
    # current active trimester
    trimestre = Trimestre.objects.filter(ativo=True).first()
    if not trimestre:
        # Tenta usar qualquer trimestre disponível
        trimestre = Trimestre.objects.filter(concluido=False).first()
        if not trimestre:
            messages.warning(request, 'Nenhum trimestre disponível. Inicie um trimestre antes de matricular alunos.')
            # Se for superintendente, direciona para iniciar um trimestre; caso contrário informa e volta ao dashboard
            if request.user.role == 'superintendente':
                return redirect('periodo_iniciar')
            else:
                return redirect('dashboard')
        messages.info(request, f'Usando trimestre: {trimestre.trimestre}/{trimestre.ano}')
    
    # CDU.008: Bloquear matrícula se trimestre foi concluído
    if trimestre.concluido:
        messages.error(request, 'Não é possível matricular alunos em um trimestre concluído.')
        return redirect('aluno_list')

    # Excluir alunos que já têm matrícula ativa em qualquer classe no trimestre atual
    matriculados_ids = Matricula.objects.filter(trimestre=trimestre, ativa=True).values_list('aluno_id', flat=True)
    alunos_disponiveis = Aluno.objects.exclude(id__in=matriculados_ids)

    if request.method == 'POST':
        # Criar novo aluno opcional
        nome = request.POST.get('nome')
        data_nasc = request.POST.get('data_nascimento')
        if nome and data_nasc:
            aluno = Aluno.objects.create(igreja=classe.igreja, nome=nome, data_nascimento=data_nasc)
            alunos_disponiveis = alunos_disponiveis | Aluno.objects.filter(id=aluno.id)

        selecionados = request.POST.getlist('alunos')
        if selecionados:
            created = 0
            for aid in selecionados:
                try:
                    aluno = Aluno.objects.get(id=aid)
                    Matricula.objects.create(aluno=aluno, trimestre=trimestre, classe=classe, ativa=True)
                    created += 1
                except Exception:
                    continue
            messages.success(request, f'{created} matrícula(s) criada(s) com sucesso.')
            # Professor volta para dashboard, outros para aluno_list
            if request.user.role == 'professor':
                return redirect('dashboard')
            else:
                return redirect('aluno_list')

    return render(request, 'aluno_matricula_form.html', {'classe': classe, 'trimestre': trimestre, 'alunos_disponiveis': alunos_disponiveis})


# @user_passes_test(is_actor)
@user_passes_test(is_secretario_or_superintendente)
# Professor, Secretário e Superintendente
def aluno_list(request):
    """Lista alunos agrupados por classe com filtro por trimestre."""
    # Obter trimestre selecionado ou usar ativo por padrão
    trimestre_selecionado_id = request.GET.get('trimestre', None)
    
    if trimestre_selecionado_id:
        try:
            trimestre_selecionado = Trimestre.objects.get(id=trimestre_selecionado_id)
        except Trimestre.DoesNotExist:
            trimestre_selecionado = Trimestre.objects.filter(ativo=True).first()
    else:
        trimestre_selecionado = Trimestre.objects.filter(ativo=True).first()
    
    # Listar todos os trimestres para dropdown
    todos_trimestres = Trimestre.objects.all().order_by('-ano', '-trimestre')
    
    # Agrupar matrículas por classe (filtrado por trimestre se selecionado)
    if trimestre_selecionado:
        matriculas = Matricula.objects.filter(trimestre=trimestre_selecionado, ativa=True).select_related('aluno', 'classe', 'trimestre')
    else:
        matriculas = Matricula.objects.none()
    
    # Agrupar por classe
    classes_com_alunos = {}
    for matricula in matriculas:
        classe = matricula.classe
        if classe.id not in classes_com_alunos:
            classes_com_alunos[classe.id] = {
                'classe': classe,
                'alunos': []
            }
        # Evitar duplicatas
        if matricula.aluno not in classes_com_alunos[classe.id]['alunos']:
            classes_com_alunos[classe.id]['alunos'].append(matricula.aluno)
    
    grupos = list(classes_com_alunos.values())
    # Ordenar por nome da classe
    grupos.sort(key=lambda x: x['classe'].nome)
    
    return render(request, 'aluno_list.html', {
        'grupos': grupos,
        'trimestre_selecionado': trimestre_selecionado,
        'todos_trimestres': todos_trimestres,
        'total_alunos': sum(len(g['alunos']) for g in grupos)
    })
    
def professor_list(request):
    professores = Professor.objects.select_related('usuario', 'classe').all()
    return render(request, 'professor_list.html', {'professores': professores})


@user_passes_test(is_superintendente)
def secretario_list(request):
    """Lista de usuários com role 'secretario'.

    Usa o modelo `Usuario` (custom user) já disponível via imports em cima.
    Renderiza um template `secretario_list.html` com a lista de secretários.
    """
    secretarios = Usuario.objects.filter(role='secretario')
    return render(request, 'secretario_list.html', {'secretarios': secretarios})


@user_passes_test(is_superintendente)
def professor_delete(request, id):
    """Remove o perfil de Professor (não remove o usuário)."""
    if request.method != 'POST':
        return redirect('professor_list')
    
    # CDU.008: Bloquear remoção de professores se trimestre ativo foi concluído
    trimestre_ativo = Trimestre.objects.filter(ativo=True).first()
    if trimestre_ativo and trimestre_ativo.concluido:
        messages.error(request, 'Não é possível remover professores em um trimestre concluído.')
        return redirect('professor_list')
    
    professor = get_object_or_404(Professor, id=id)
    username = getattr(professor.usuario, 'username', str(professor.id))
    try:
        professor.delete()
        messages.success(request, f'Professor {username} removido com sucesso.')
    except Exception as e:
        messages.error(request, f'Erro ao remover professor: {e}')
    return redirect('professor_list')


@user_passes_test(is_superintendente)
def secretario_delete(request, id):
    """Remove o usuário secretariado (apaga o Usuario)."""
    if request.method != 'POST':
        return redirect('secretario_list')
    usuario = get_object_or_404(Usuario, id=id)
    username = usuario.username
    try:
        usuario.delete()
        messages.success(request, f'Secretário {username} removido com sucesso.')
    except Exception as e:
        messages.error(request, f'Erro ao remover secretário: {e}')
    return redirect('secretario_list')

@user_passes_test(is_secretario_or_superintendente)
def aluno_transferir(request, id):
    # Transferir matrícula para outra classe no trimestre vigente
    aluno = get_object_or_404(Aluno, id=id)
    # Prioriza trimestre informado via parâmetro GET/POST (preserva contexto da listagem)
    trimestre_id = request.GET.get('trimestre') or request.POST.get('trimestre')
    trimestre = None
    if trimestre_id:
        try:
            trimestre = Trimestre.objects.get(id=trimestre_id)
        except Trimestre.DoesNotExist:
            trimestre = None

    # Se não foi fornecido, cai para o trimestre ativo (modo anterior)
    if not trimestre:
        trimestre = Trimestre.objects.filter(ativo=True).first()

    if not trimestre:
        # Mantemos mensagem informativa — redirecionamos para a lista de alunos
        messages.error(request, 'Não há trimestre selecionado nem trimestre ativo. Peça ao superintendente para iniciar um trimestre ou selecione um trimestre válido na lista.')
        return redirect('aluno_list')
    
    # CDU.008: Bloquear transferência se trimestre foi concluído
    if trimestre.concluido:
        messages.error(request, 'Não é possível transferir alunos em um trimestre concluído.')
        return redirect('aluno_list')

    if request.method == 'POST':
        nova_classe_id = request.POST.get('classe')
        # manter o trimestre informado no POST, se veio no formulário
        trimestre_id = request.POST.get('trimestre') or trimestre_id
        if trimestre_id:
            try:
                trimestre = Trimestre.objects.get(id=trimestre_id)
            except Trimestre.DoesNotExist:
                # fallback para o trimestre já carregado
                pass
        nova_classe = get_object_or_404(Classe, id=nova_classe_id)
        # Inativar matrículas anteriores
        Matricula.objects.filter(aluno=aluno, trimestre=trimestre).update(ativa=False)

        # Evitar duplicação por unique_together: reutilizar matrícula existente ou criar nova
        try:
            matricula, created = Matricula.objects.get_or_create(
                aluno=aluno,
                trimestre=trimestre,
                classe=nova_classe,
                defaults={'ativa': True}
            )
            if not created:
                # caso já existisse, reativa
                matricula.ativa = True
                matricula.save()
        except Exception as e:
            # captura erros inesperados (incluindo rare race conditions) e informa o usuário
            messages.error(request, f'Erro ao transferir aluno (detalhe técnico): {e}')
            return redirect(f"{reverse('aluno_list')}?trimestre={trimestre.id}" if trimestre else reverse('aluno_list'))
        messages.success(request, 'Aluno transferido com sucesso.')
        # redireciona de volta para a lista de alunos preservando o trimestre
        if trimestre:
            return redirect(f"{reverse('aluno_list')}?trimestre={trimestre.id}")
        return redirect('aluno_list')

    classes = Classe.objects.all()
    return render(request, 'aluno_transferir_form.html', {'aluno': aluno, 'classes': classes, 'trimestre': trimestre})

@user_passes_test(is_professor)
def aluno_list_professor(request):
    """Professor lista alunos da sua classe"""
    try:
        professor = Professor.objects.get(usuario=request.user)
    except Professor.DoesNotExist:
        messages.error(request, 'Você não está vinculado a nenhuma classe.')
        return redirect('dashboard')
    
    # Obter trimestre selecionado ou usar ativo por padrão
    trimestre_selecionado_id = request.GET.get('trimestre', None)
    
    if trimestre_selecionado_id:
        try:
            trimestre_selecionado = Trimestre.objects.get(id=trimestre_selecionado_id)
        except Trimestre.DoesNotExist:
            trimestre_selecionado = Trimestre.objects.filter(ativo=True).first()
    else:
        trimestre_selecionado = Trimestre.objects.filter(ativo=True).first()
    
    # Listar todos os trimestres para dropdown
    todos_trimestres = Trimestre.objects.all().order_by('-ano', '-trimestre')
    
    # Matrículas ativas da classe do professor no trimestre selecionado
    if trimestre_selecionado:
        matriculas = Matricula.objects.filter(
            classe=professor.classe,
            trimestre=trimestre_selecionado,
            ativa=True
        ).select_related('aluno', 'classe', 'trimestre')
    else:
        matriculas = Matricula.objects.none()
    
    alunos = [m.aluno for m in matriculas]
    
    return render(request, 'aluno_list_professor.html', {
        'alunos': alunos,
        'classe': professor.classe,
        'trimestre_selecionado': trimestre_selecionado,
        'todos_trimestres': todos_trimestres
    })

@user_passes_test(is_secretario_or_superintendente)
def aula_concluir(request, id):
    # Somente via POST para evitar conclusões acidentais por GET
    if request.method != 'POST':
        return redirect('relatorio_aula', id=id)
    aula = get_object_or_404(Aula, id=id)
    
    # CDU.008: Bloquear conclusão de aula se trimestre foi concluído
    if aula.trimestre.concluido:
        messages.error(request, 'Não é possível concluir aulas em um trimestre concluído.')
        return redirect('relatorio_aula', id=id)
    
    try:
        aula.concluida = True
        aula.save()
        messages.success(request, 'Aula marcada como concluída com sucesso.')
    except Exception as e:
        messages.error(request, f'Erro ao concluir aula: {e}')
    return redirect('relatorio_aula', id=id)

@user_passes_test(is_secretario_or_superintendente)
def relatorio_aula(request, id):
    aula = get_object_or_404(Aula, id=id)
    diarios = Diario.objects.filter(aula=aula)
    # soma dos valores
    resumo = {
        'alunos_presentes': sum(d.alunos_presentes for d in diarios),
        'alunos_ausentes': sum(d.alunos_ausentes for d in diarios),
        'visitantes': sum(d.visitantes for d in diarios),
        'biblias': sum(d.biblias for d in diarios),
        'revistas': sum(d.revistas for d in diarios),
        'ofertas': sum(d.ofertas for d in diarios),
        'dizimos': sum(d.dizimos for d in diarios),
    }
    return render(request, 'relatorio_aula.html', {'aula': aula, 'diarios': diarios, 'resumo': resumo})

@user_passes_test(is_secretario_or_superintendente)
def relatorio_trimestre(request):
    periodos = Trimestre.objects.filter(concluido=True).order_by('-ano', '-trimestre')
    # Calcula resumo por trimestre (agrega dados de todos os diarios das aulas daquele trimestre)
    resumos = []
    for periodo in periodos:
        diarios = Diario.objects.filter(aula__trimestre=periodo)
        resumo = {
            'alunos_presentes': sum(d.alunos_presentes for d in diarios),
            'alunos_ausentes': sum(d.alunos_ausentes for d in diarios),
            'visitantes': sum(d.visitantes for d in diarios),
            'biblias': sum(d.biblias for d in diarios),
            'revistas': sum(d.revistas for d in diarios),
            'ofertas': sum(d.ofertas for d in diarios),
            'dizimos': sum(d.dizimos for d in diarios),
            'total_diarios': diarios.count(),
            'periodo': periodo,
        }
        resumos.append(resumo)
    return render(request, 'relatorio_trimestre.html', {'periodos': periodos, 'resumos': resumos})

# --- Professor ---
# ... (mantenha os outros imports, como Aula e Professor)

@user_passes_test(is_professor)
def aula_list_professor(request):
    professor_logado = getattr(request.user, 'professor', None)
    if professor_logado:
        classe_do_professor = professor_logado.classe
        aulas = Aula.objects.filter(classe=classe_do_professor).order_by('data_prevista')
    else:
        aulas = Aula.objects.none()

    return render(request, 'aula_list_professor.html', {'aulas': aulas})

@user_passes_test(is_actor)
def diario_registro(request, aula_id):
    aula = get_object_or_404(Aula, id=aula_id)
    # Não permitir registro/edição se a aula já foi concluída
    if aula.concluida:
        messages.error(request, 'Esta aula já foi concluída; não é possível editar o diário.')
        # Professor volta para lista de aulas, outros para relatório
        if request.user.role == 'professor':
            return redirect('aula_list_professor')
        else:
            return redirect('aula_list')
    
    # Não permitir edição se o trimestre foi concluído
    if aula.trimestre.concluido:
        messages.error(request, 'O trimestre foi concluído; não é possível editar o diário.')
        # Professores não têm permissão para relatorio_aula, redirecionar conforme role
        if request.user.role == 'professor':
            return redirect('aula_list_professor')
        else:
            return redirect('relatorio_aula', id=aula.id)
    
    diario, created = Diario.objects.get_or_create(aula=aula)

    # Use the trimestre associated with the aula (CDU.002): diário está ligado à aula/trimestre
    trimestre = aula.trimestre
    if not trimestre or not trimestre.ativo:
        messages.error(request, 'O trimestre da aula não está ativo; impossível editar o diário.')
        if request.user.role == 'professor':
            return redirect('aula_list_professor')
        else:
            return redirect('aula_list')

    matriculas = Matricula.objects.filter(classe=aula.classe, trimestre=trimestre, ativa=True)
    alunos = [m.aluno for m in matriculas]

    if request.method == 'POST':
        # processa presenças e dados do diário (CDU.002)
        presentes = request.POST.getlist('presente')  # list of aluno ids marked present
        visitantes = int(request.POST.get('visitantes') or 0)
        biblias = int(request.POST.get('biblias') or 0)
        revistas = int(request.POST.get('revistas') or 0)
        ofertas = float(request.POST.get('ofertas') or 0)
        dizimos = float(request.POST.get('dizimos') or 0)
        observacoes = request.POST.get('observacoes')

        # atualiza diario (CDU.002)
        diario.visitantes = visitantes
        diario.biblias = biblias
        diario.revistas = revistas
        diario.ofertas = ofertas
        diario.dizimos = dizimos
        diario.observacoes = observacoes

        # criar/atualizar presencas
        presentes_set = set(int(x) for x in presentes)
        alunos_presentes = 0
        for aluno in alunos:
            status = 'P' if aluno.id in presentes_set else 'F'
            pres, _ = Presenca.objects.update_or_create(aluno=aluno, diario=diario, defaults={'status': status})
            if status == 'P':
                alunos_presentes += 1

        diario.alunos_presentes = alunos_presentes
        diario.alunos_ausentes = len(alunos) - alunos_presentes
        diario.save()

        messages.success(request, 'Diário salvo com sucesso.')
        # Professor volta para lista de aulas, outros para relatório
        if request.user.role == 'professor':
            return redirect('aula_list_professor')
        else:
            return redirect('relatorio_aula', id=aula.id)

    presencas = {p.aluno_id: p for p in Presenca.objects.filter(diario=diario)}
    return render(request, 'diario_registro_form.html', {'aula': aula, 'diario': diario, 'alunos': alunos, 'presencas': presencas})

@user_passes_test(is_secretario_or_superintendente)
def aula_list(request):
    """Listagem de aulas para Secretário/Superintendente (gerenciar e concluir aulas)."""
    aulas = Aula.objects.all().order_by('-data_prevista')
    return render(request, 'aula_list.html', {'aulas': aulas})

@user_passes_test(is_actor)
def diario_presenca(request, aula_id):
    diario = get_object_or_404(Diario, aula_id=aula_id)
    presencas = Presenca.objects.filter(diario=diario)
    return render(request, 'diario_presenca_form.html', {'presencas': presencas})

# CDU.007 - Criar aulas para o trimestre
@user_passes_test(is_superintendente)
def periodo_criar_aulas(request, trimestre_id):
    """Cria aulas para um trimestre recém-iniciado (CDU.007)."""
    trimestre = get_object_or_404(Trimestre, id=trimestre_id)
    
    # CDU.008: Bloquear criação de aulas se trimestre foi concluído
    if trimestre.concluido:
        messages.error(request, 'Não é possível criar aulas em um trimestre concluído.')
        return redirect('periodo_list')
    
    if request.method == 'POST':
        # Criar aulas baseado no formulário
        classes = Classe.objects.filter(igreja=trimestre.igreja)
        
        # Coleta dados de todas as aulas
        aula_count = int(request.POST.get('aula_count', 0))
        aulas_criadas = 0
        
        for i in range(1, aula_count + 1):
            titulo = request.POST.get(f'titulo_{i}', '').strip()
            data_str = request.POST.get(f'data_{i}', '')
            
            if not titulo or not data_str:
                continue
                
            try:
                from datetime import datetime
                data_prevista = datetime.strptime(data_str, '%Y-%m-%d').date()
                
                # Criar aula para cada classe do trimestre
                for classe in classes:
                    Aula.objects.create(
                        trimestre=trimestre,
                        classe=classe,
                        titulo=titulo,
                        data_prevista=data_prevista,
                        concluida=False
                    )
                aulas_criadas += len(classes)
            except Exception as e:
                messages.warning(request, f'Erro ao criar aula "{titulo}": {str(e)}')
                continue
        
        if aulas_criadas > 0:
            messages.success(request, f'{aulas_criadas} aula(s) criada(s) com sucesso!')
            return redirect('periodo_list')
        else:
            messages.error(request, 'Nenhuma aula foi criada. Verifique os dados.')
    
    return render(request, 'periodo_criar_aulas.html', {'trimestre': trimestre})

