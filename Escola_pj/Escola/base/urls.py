from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='home'),  # raiz -> dashboard
    path('home/', views.dashboard, name='dashboard'), ## Home

    # Superintendente
    path('professor/cadastrar/', views.cadastrar_professor, name='cadastrar_professor'),

    path('classes/list/', views.classe_list, name='classe_list'),
    path('classes/create/', views.classe_create, name='classe_create'),
    path('classes/<int:id>/edit/', views.classe_create, name='classe_edit'),
    path('periodos/list/', views.periodo_list, name='periodo_list'),
    path('periodos/iniciar/', views.periodo_iniciar, name='periodo_iniciar'),
    path('periodos/<int:trimestre_id>/criar-aulas/', views.periodo_criar_aulas, name='periodo_criar_aulas'),
    path('secretarios/list/', views.secretario_list, name='secretario_list'),
    path('secretarios/<int:id>/excluir/', views.secretario_delete, name='secretario_delete'),
    
    # Concluir via POST a partir da listagem (seleção)
    path('periodos/concluir/', views.periodo_concluir, name='periodo_concluir'),
    path('alunos/list/', views.aluno_list, name='aluno_list'),
    path('professores/list/', views.professor_list, name='professor_list'),
    path('professores/<int:id>/excluir/', views.professor_delete, name='professor_delete'),

    # Secretário
    path('alunos/matricular/', views.aluno_matricular, name='aluno_matricular'),
    path('alunos/matricular/<int:classe_id>/', views.aluno_matricular, name='aluno_matricular_classe'),
    path('alunos/<int:id>/transferir/', views.aluno_transferir, name='aluno_transferir'),
    path('alunos/minha-classe/', views.aluno_list_professor, name='aluno_list_professor'),
    path('aulas/<int:id>/concluir/', views.aula_concluir, name='aula_concluir'),
    path('relatorios/aula/<int:id>/', views.relatorio_aula, name='relatorio_aula'),
    path('relatorios/trimestre/', views.relatorio_trimestre, name='relatorio_trimestre'),

    # Secretário e Superintendente
    path('aulas/list/', views.aula_list, name='aula_list'),

    # Professor
    path('professor/minhas-aulas/', views.aula_list_professor, name='aula_list_professor'),
    path('diario/<int:aula_id>/', views.diario_registro, name='diario_registro'),
    path('diario/<int:aula_id>/chamada/', views.diario_presenca, name='diario_presenca'),
]
