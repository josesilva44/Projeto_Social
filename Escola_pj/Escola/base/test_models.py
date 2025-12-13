from datetime import date
from .test_utils import BaseTestCase

from .models import (
    Igreja, Usuario, Classe, Trimestre, Professor, Aluno,
    Matricula, Aula, Diario, Presenca
)


class IgrejaTestCase(BaseTestCase):
    """Testes para o modelo Igreja"""
    
    def setUp(self):
        super().setUp()
        self.igreja = Igreja.objects.create(nome="Igreja Central")
    
    def test_criar_igreja(self):
        """Verifica se uma Igreja pode ser criada"""
        self.assertEqual(self.igreja.nome, "Igreja Central")
    
    def test_string_representation(self):
        """Verifica a representação em string da Igreja"""
        self.assertEqual(str(self.igreja), "Igreja Central")
    
    def test_igreja_unica(self):
        """Verifica se não é possível criar duas igrejas com o mesmo nome"""
        with self.assertRaises(Exception):
            Igreja.objects.create(nome="Igreja Central")


class UsuarioTestCase(BaseTestCase):
    """Testes para o modelo Usuario (Custom User)"""
    
    def setUp(self):
        super().setUp()
    
    def test_criar_usuario_superintendente(self):
        """Verifica a criação de um usuário superintendente"""
        user = self.create_user(
            username="super",
            email="super@test.com",
            password="senha123",
            role='superintendente',
            igreja=self.igreja
        )
        self.assertEqual(user.role, 'superintendente')
        self.assertEqual(user.igreja, self.igreja)
    
    def test_criar_usuario_secretario(self):
        """Verifica a criação de um usuário secretário"""
        user = self.create_user(
            username="secretario",
            email="sec@test.com",
            password="senha123",
            role='secretario',
            igreja=self.igreja
        )
        self.assertEqual(user.role, 'secretario')
    
    def test_criar_usuario_professor(self):
        """Verifica a criação de um usuário professor"""
        user = self.create_user(
            username="professor",
            email="prof@test.com",
            password="senha123",
            role='professor',
            igreja=self.igreja
        )
        self.assertEqual(user.role, 'professor')
    
    def test_string_representation(self):
        """Verifica a representação em string do Usuário"""
        user = self.create_user(
            username="test",
            password="senha123",
            role='professor'
        )
        self.assertIn("test", str(user))
        self.assertIn("Professor", str(user))


class ClasseTestCase(BaseTestCase):
    """Testes para o modelo Classe"""
    
    def setUp(self):
        super().setUp()
        self.classe = self.create_classe()
    
    def test_criar_classe(self):
        """Verifica se uma Classe pode ser criada"""
        self.assertEqual(self.classe.nome, "Classe A")
        self.assertEqual(self.classe.igreja, self.igreja)
    
    def test_string_representation(self):
        """Verifica a representação em string da Classe"""
        self.assertIn("Classe A", str(self.classe))
        self.assertIn("Igreja Teste", str(self.classe))


class TrimestreTestCase(BaseTestCase):
    """Testes para o modelo Trimestre"""
    
    def setUp(self):
        super().setUp()
        self.trimestre = self.create_trimestre()
    
    def test_criar_trimestre(self):
        """Verifica se um Trimestre pode ser criado"""
        self.assertEqual(self.trimestre.trimestre, "1º Trimestre")
        self.assertEqual(self.trimestre.ano, 2024)
        self.assertTrue(self.trimestre.ativo)
    
    def test_apenas_um_trimestre_ativo(self):
        """Verifica se apenas um trimestre pode estar ativo por Igreja"""
        novo_trimestre = Trimestre.objects.create(
            igreja=self.igreja,
            trimestre="2º Trimestre",
            ano=2024,
            ativo=True
        )
        # Recarrega o primeiro trimestre do banco
        self.trimestre.refresh_from_db()
        self.assertFalse(self.trimestre.ativo)
        self.assertTrue(novo_trimestre.ativo)


class ProfessorTestCase(BaseTestCase):
    """Testes para o modelo Professor"""
    
    def setUp(self):
        super().setUp()
        self.classe = self.create_classe()
        self.usuario = self.create_user(username='professor1', role='professor')
        self.professor = Professor.objects.create(usuario=self.usuario, classe=self.classe)
    
    def test_criar_professor(self):
        """Verifica se um Professor pode ser criado"""
        self.assertEqual(self.professor.usuario, self.usuario)
        self.assertEqual(self.professor.classe, self.classe)


class AlunoTestCase(BaseTestCase):
    """Testes para o modelo Aluno"""
    
    def setUp(self):
        super().setUp()
        self.aluno = self.create_aluno()
    
    def test_criar_aluno(self):
        """Verifica se um Aluno pode ser criado"""
        self.assertEqual(self.aluno.nome, "João Silva")
        self.assertEqual(self.aluno.data_nascimento, date(2010, 5, 15))
    
    def test_string_representation(self):
        """Verifica a representação em string do Aluno"""
        self.assertEqual(str(self.aluno), "João Silva")


class MatriculaTestCase(BaseTestCase):
    """Testes para o modelo Matrícula"""
    
    def setUp(self):
        super().setUp()
        self.classe = self.create_classe()
        self.trimestre = self.create_trimestre()
        self.aluno = self.create_aluno()
        self.matricula = self.create_matricula(self.aluno, self.trimestre, self.classe)
    
    def test_criar_matricula(self):
        """Verifica se uma Matrícula pode ser criada"""
        self.assertEqual(self.matricula.aluno, self.aluno)
        self.assertEqual(self.matricula.classe, self.classe)
        self.assertTrue(self.matricula.ativa)


class AulaTestCase(BaseTestCase):
    """Testes para o modelo Aula"""
    
    def setUp(self):
        super().setUp()
        self.classe = self.create_classe()
        self.trimestre = self.create_trimestre()
        self.aula = self.create_aula(self.trimestre, self.classe)
    
    def test_criar_aula(self):
        """Verifica se uma Aula pode ser criada"""
        self.assertEqual(self.aula.titulo, "Aula 1")
        self.assertFalse(self.aula.concluida)


class DiarioTestCase(BaseTestCase):
    """Testes para o modelo Diário"""
    
    def setUp(self):
        super().setUp()
        self.classe = self.create_classe()
        self.trimestre = self.create_trimestre()
        self.aula = self.create_aula(self.trimestre, self.classe)
        self.diario = self.create_diario(self.aula, alunos_presentes=10, alunos_ausentes=2, visitantes=1, biblias=8, revistas=5, ofertas=50.00, dizimos=100.00)
    
    def test_criar_diario(self):
        """Verifica se um Diário pode ser criado"""
        self.assertEqual(self.diario.alunos_presentes, 10)
        self.assertEqual(self.diario.alunos_ausentes, 2)


class PresencaTestCase(BaseTestCase):
    """Testes para o modelo Presença"""
    
    def setUp(self):
        super().setUp()
        self.classe = self.create_classe()
        self.trimestre = self.create_trimestre()
        self.aula = self.create_aula(self.trimestre, self.classe)
        self.diario = self.create_diario(self.aula)
        self.aluno = self.create_aluno()
        self.presenca = self.create_presenca(self.aluno, self.diario)
    
    def test_criar_presenca(self):
        """Verifica se uma Presença pode ser criada"""
        self.assertEqual(self.presenca.aluno, self.aluno)
        self.assertEqual(self.presenca.status, 'P')
