from .test_utils import BaseTestCase
from django.urls import reverse
from datetime import date

from .models import (
    Igreja, Usuario, Classe, Trimestre, Professor, Aluno,
    Matricula, Aula, Diario, Presenca
)


# ============== TESTES DE VIEWS ==============

class DashboardViewTestCase(BaseTestCase):
    """Testes para a view dashboard"""
    
    def setUp(self):
        super().setUp()
        # Criar usuários
        self.superintendente = self.create_user(
            username="super",
            password="senha123",
            role='superintendente',
            igreja=self.igreja
        )
        self.secretario = self.create_user(
            username="secretario",
            password="senha123",
            role='secretario',
            igreja=self.igreja
        )
        self.professor_user = self.create_user(
            username="professor",
            password="senha123",
            role='professor',
            igreja=self.igreja
        )
        
        # Criar classe e professor
        self.classe = self.create_classe()
        self.professor = Professor.objects.create(usuario=self.professor_user, classe=self.classe)
    
    def test_dashboard_not_logged_in(self):
        """Verifica se usuário não autenticado é redirecionado"""
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login/', response.url)
    
    def test_dashboard_superintendente(self):
        """Verifica se superintendente vê o dashboard correto"""
        self.client.login(username='super', password='senha123')
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'tela_inicial/dashboard_superintendente.html')
        self.assertIn('perfil', response.context)
        self.assertEqual(response.context['perfil'], 'Superintendente')
    
    def test_dashboard_secretario(self):
        """Verifica se secretário vê o dashboard correto"""
        self.client.login(username='secretario', password='senha123')
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'tela_inicial/dashboard_secretario.html')
        self.assertIn('perfil', response.context)
        self.assertEqual(response.context['perfil'], 'Secretário')
    
    def test_dashboard_professor(self):
        """Verifica se professor vê o dashboard correto"""
        self.client.login(username='professor', password='senha123')
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'tela_inicial/dashboard_professor.html')
        self.assertIn('perfil', response.context)
        self.assertEqual(response.context['perfil'], 'Professor')


class ClasseViewTestCase(BaseTestCase):
    """Testes para as views de Classe"""
    
    def setUp(self):
        super().setUp()
        self.superintendente = self.create_user(
            username="super",
            password="senha123",
            role='superintendente'
        )
        self.classe = self.create_classe()
    
    def test_classe_list_view(self):
        """Verifica a listagem de classes"""
        self.client.login(username='super', password='senha123')
        response = self.client.get(reverse('classe_list'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'classe_list.html')
        self.assertIn('classes', response.context)
        self.assertEqual(len(response.context['classes']), 1)
    
    def test_classe_list_not_authenticated(self):
        """Verifica se usuário não autenticado não acessa lista de classes"""
        response = self.client.get(reverse('classe_list'))
        self.assertEqual(response.status_code, 302)
    
    def test_classe_list_not_superintendente(self):
        """Verifica se apenas superintendente acessa lista de classes"""
        professor = self.create_user(
            username="professor",
            password="senha123",
            role='professor'
        )
        self.client.login(username='professor', password='senha123')
        response = self.client.get(reverse('classe_list'))
        self.assertEqual(response.status_code, 302)


class TrimestreViewTestCase(BaseTestCase):
    """Testes para as views de Trimestre"""
    
    def setUp(self):
        super().setUp()
        self.superintendente = self.create_user(
            username="super",
            password="senha123",
            role='superintendente'
        )
        self.trimestre = self.create_trimestre()
    
    def test_periodo_list_view(self):
        """Verifica a listagem de períodos"""
        self.client.login(username='super', password='senha123')
        response = self.client.get(reverse('periodo_list'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'periodo_list.html')
        self.assertIn('periodos', response.context)
    
    def test_periodo_iniciar_get(self):
        """Verifica a exibição do formulário para iniciar período"""
        self.client.login(username='super', password='senha123')
        response = self.client.get(reverse('periodo_iniciar'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'periodo_iniciar.html')
    
    def test_periodo_iniciar_post(self):
        """Verifica a criação de um novo período"""
        self.client.login(username='super', password='senha123')
        response = self.client.post(reverse('periodo_iniciar'), {
            'nome': '2',
            'ano': 2024,
            'igreja': self.igreja.id
        })
        self.assertEqual(response.status_code, 302)  # Redirecionamento
        self.assertTrue(Trimestre.objects.filter(trimestre="2º Trimestre").exists())


class AlunoViewTestCase(BaseTestCase):
    """Testes para as views de Aluno"""
    
    def setUp(self):
        super().setUp()
        self.classe = self.create_classe()
        self.trimestre = self.create_trimestre()
        self.aluno = self.create_aluno()
        self.matricula = self.create_matricula(self.aluno, self.trimestre, self.classe)
        self.secretario = self.create_user(username='secretario', role='secretario')
    
    def test_aluno_list_view(self):
        """Verifica a listagem de alunos"""
        self.client.login(username='secretario', password='senha123')
        response = self.client.get(reverse('aluno_list'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'aluno_list.html')
        self.assertIn('grupos', response.context)
    
    def test_aluno_matricular_select_classe(self):
        """Verifica a seleção de classe para matrícula"""
        self.client.login(username='secretario', password='senha123')
        response = self.client.get(reverse('aluno_matricular'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'aluno_matricula_select_classe.html')


class ProfessorViewTestCase(BaseTestCase):
    """Testes para as views de Professor"""
    
    def setUp(self):
        super().setUp()
        self.classe = self.create_classe()
        self.professor_user = self.create_user(username='professor', role='professor')
        self.professor = Professor.objects.create(usuario=self.professor_user, classe=self.classe)
        self.superintendente = self.create_user(username='super', role='superintendente')
    
    def test_professor_list_view(self):
        """Verifica a listagem de professores"""
        self.client.login(username='super', password='senha123')
        response = self.client.get(reverse('professor_list'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'professor_list.html')
        self.assertIn('professores', response.context)
        self.assertEqual(len(response.context['professores']), 1)


class AulaViewTestCase(BaseTestCase):
    """Testes para as views de Aula"""
    
    def setUp(self):
        super().setUp()
        self.classe = self.create_classe()
        self.trimestre = self.create_trimestre()
        self.aula = self.create_aula(self.trimestre, self.classe)
        self.professor_user = self.create_user(username='professor', role='professor')
        self.professor = Professor.objects.create(usuario=self.professor_user, classe=self.classe)
    
    def test_aula_list_professor_view(self):
        """Verifica a listagem de aulas para professor"""
        self.client.login(username='professor', password='senha123')
        response = self.client.get(reverse('aula_list_professor'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'aula_list_professor.html')
        self.assertIn('aulas', response.context)


class DiarioViewTestCase(BaseTestCase):
    """Testes para as views de Diário"""
    
    def setUp(self):
        super().setUp()
        self.classe = self.create_classe()
        self.trimestre = self.create_trimestre()
        self.aula = self.create_aula(self.trimestre, self.classe)
        self.aluno1 = self.create_aluno(nome='João Silva')
        self.aluno2 = self.create_aluno(nome='Maria Santos')
        self.matricula1 = self.create_matricula(self.aluno1, self.trimestre, self.classe)
        self.matricula2 = self.create_matricula(self.aluno2, self.trimestre, self.classe)
        self.professor_user = self.create_user(username='professor', role='professor')
        self.professor = Professor.objects.create(usuario=self.professor_user, classe=self.classe)
    
    def test_diario_registro_view_get(self):
        """Verifica a exibição do formulário de registro de diário"""
        self.client.login(username='professor', password='senha123')
        response = self.client.get(reverse('diario_registro', args=[self.aula.id]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'diario_registro_form.html')
        self.assertIn('aula', response.context)
        self.assertIn('alunos', response.context)
    
    def test_diario_registro_view_post(self):
        """Verifica o registro de diário com presenças"""
        self.client.login(username='professor', password='senha123')
        response = self.client.post(reverse('diario_registro', args=[self.aula.id]), {
            'presente': [str(self.aluno1.id)],
            'visitantes': 1,
            'biblias': 8,
            'revistas': 5,
            'ofertas': 50.00,
            'dizimos': 100.00,
            'observacoes': 'Aula normal'
        })
        self.assertEqual(response.status_code, 302)  # Redirecionamento
        
        # Verifica se o diário foi criado/atualizado
        diario = Diario.objects.get(aula=self.aula)
        self.assertEqual(diario.alunos_presentes, 1)
        self.assertEqual(diario.alunos_ausentes, 1)
        self.assertEqual(diario.visitantes, 1)
        
        # Verifica as presenças
        presenca_presente = Presenca.objects.get(aluno=self.aluno1, diario=diario)
        self.assertEqual(presenca_presente.status, 'P')
        
        presenca_ausente = Presenca.objects.get(aluno=self.aluno2, diario=diario)
        self.assertEqual(presenca_ausente.status, 'F')


class RelatorioViewTestCase(BaseTestCase):
    """Testes para as views de Relatório"""
    
    def setUp(self):
        super().setUp()
        self.classe = self.create_classe()
        self.trimestre = self.create_trimestre(concluido=True)
        self.aula = self.create_aula(self.trimestre, self.classe, concluida=True)
        self.diario = self.create_diario(self.aula, alunos_presentes=10, alunos_ausentes=2)
        self.secretario = self.create_user(username='secretario', role='secretario')
    
    def test_relatorio_aula_view(self):
        """Verifica a exibição do relatório de aula"""
        self.client.login(username='secretario', password='senha123')
        response = self.client.get(reverse('relatorio_aula', args=[self.aula.id]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'relatorio_aula.html')
        self.assertIn('aula', response.context)
        self.assertIn('resumo', response.context)
        self.assertEqual(response.context['resumo']['alunos_presentes'], 10)
    
    def test_relatorio_trimestre_view(self):
        """Verifica a exibição do relatório de trimestre"""
        self.client.login(username='secretario', password='senha123')
        response = self.client.get(reverse('relatorio_trimestre'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'relatorio_trimestre.html')
        self.assertIn('periodos', response.context)


# ============== TESTES DE INTEGRAÇÃO ==============

class IntegracaoFluxoAulaTestCase(BaseTestCase):
    """Testes de integração para o fluxo completo de aula"""
    
    def setUp(self):
        super().setUp()
        self.classe = self.create_classe()
        self.trimestre = self.create_trimestre()
        
        # Criar alunos
        self.aluno1 = self.create_aluno(nome='João Silva')
        self.aluno2 = self.create_aluno(nome='Maria Santos')
        
        # Matricular alunos
        self.create_matricula(self.aluno1, self.trimestre, self.classe)
        self.create_matricula(self.aluno2, self.trimestre, self.classe)
        
        # Criar professor
        self.professor_user = self.create_user(username='professor', role='professor')
        self.professor = Professor.objects.create(
            usuario=self.professor_user,
            classe=self.classe
        )
        
        # Criar aula
        self.aula = self.create_aula(self.trimestre, self.classe, titulo='Aula de Integração')
    
    def test_fluxo_completo_aula(self):
        """Testa o fluxo completo: criar aula -> registrar diário -> marcar como concluída"""
        
        # 1. Professor acessa a aula
        self.client.login(username='professor', password='senha123')
        response = self.client.get(reverse('aula_list_professor'))
        self.assertEqual(response.status_code, 200)
        self.assertIn(self.aula, response.context['aulas'])
        
        # 2. Professor registra o diário
        response = self.client.post(reverse('diario_registro', args=[self.aula.id]), {
            'presente': [str(self.aluno1.id)],
            'visitantes': 0,
            'biblias': 8,
            'revistas': 5,
            'ofertas': 50.00,
            'dizimos': 100.00,
            'observacoes': 'Aula normal'
        })
        self.assertEqual(response.status_code, 302)
        
        # 3. Verifica se o diário foi criado
        diario = Diario.objects.get(aula=self.aula)
        self.assertEqual(diario.alunos_presentes, 1)
        self.assertEqual(diario.alunos_ausentes, 1)
        
        # 4. Secretário marca a aula como concluída
        secretario = Usuario.objects.create_user(
            username="secretario",
            password="senha123",
            role='secretario',
            igreja=self.igreja
        )
        self.client.logout()
        self.client.login(username='secretario', password='senha123')
        
        response = self.client.post(reverse('aula_concluir', args=[self.aula.id]))
        self.assertEqual(response.status_code, 302)
        
        # 5. Verifica se a aula foi marcada como concluída
        self.aula.refresh_from_db()
        self.assertTrue(self.aula.concluida)
        
        # 6. Verifica o relatório da aula
        response = self.client.get(reverse('relatorio_aula', args=[self.aula.id]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['resumo']['alunos_presentes'], 1)
