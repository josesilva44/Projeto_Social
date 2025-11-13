from django.db import models
from django.utils import timezone
from django.contrib.auth.models import AbstractUser


class Igreja(models.Model):
    nome = models.CharField("Nome da Igreja", max_length=100, unique=True)

    class Meta:
        verbose_name = "Igreja"
        verbose_name_plural = "Igrejas"
        ordering = ["nome"]

    def __str__(self):
        return self.nome


class Usuario(AbstractUser):
    ROLE_CHOICES = [
        ('superintendente', 'Superintendente'),
        ('secretario', 'Secretário'),
        ('professor', 'Professor'),
    ]

    igreja = models.ForeignKey(Igreja, on_delete=models.PROTECT, related_name="usuarios", null=True, blank=True)
    role = models.CharField("Cargo", max_length=50, choices=ROLE_CHOICES, default='professor')

    class Meta:
        verbose_name = "Usuário"
        verbose_name_plural = "Usuários"

    #Nome, Email, Cargo

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"


# CLASSE
# ==================
class Classe(models.Model):
    igreja = models.ForeignKey(Igreja, on_delete=models.PROTECT, related_name="classes")
    nome = models.CharField("Nome da Classe", max_length=100)
    #descricao = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name = "Classe"
        verbose_name_plural = "Classes"
        ordering = ["igreja", "nome"]

    def __str__(self):
        return f"{self.nome} ({self.igreja.nome})"


# TRIMESTRE
# ==================
class Trimestre(models.Model):
    igreja = models.ForeignKey(Igreja, on_delete=models.PROTECT, related_name="trimestres")
    trimestre = models.CharField(max_length=50)  # 1 Trim
    ano = models.PositiveIntegerField()
    ativo = models.BooleanField(default=False)
    concluido = models.BooleanField(default=False)

    class Meta:
        verbose_name = "Trimestre"
        verbose_name_plural = "Trimestres"
        unique_together = ('igreja', 'trimestre', 'ano')
        ordering = ["-ano", "trimestre"]

    def __str__(self):
        status = "Concluído" if self.concluido else "Ativo" if self.ativo else "Inativo"
        return f"{self.trimestre}/{self.ano} - {self.igreja.nome} ({status})"



# PROFESSOR
# ==================
class Professor(models.Model):
    usuario = models.OneToOneField(Usuario, on_delete=models.CASCADE, limit_choices_to={'role': 'professor'})
    classe = models.ForeignKey(Classe, on_delete=models.PROTECT, related_name="professores")

    class Meta:
        verbose_name = "Professor"
        verbose_name_plural = "Professores"

    def __str__(self):
        return f"{self.usuario.get_full_name()} - {self.classe.nome}"



# AULA
# ==================
class Aula(models.Model):
    trimestre = models.ForeignKey(Trimestre, on_delete=models.PROTECT, related_name="aulas")
    classe = models.ForeignKey(Classe, on_delete=models.PROTECT, related_name="aulas")
    titulo = models.CharField("Título da Aula", max_length=200)
    data_prevista = models.DateField(default=timezone.now)
    concluida = models.BooleanField(default=False)

    class Meta:
        verbose_name = "Aula"
        verbose_name_plural = "Aulas"
        ordering = ["data_prevista"]

    def __str__(self):
        return f"{self.titulo} - {self.classe.nome} ({self.trimestre})"



# ALUNO
# ==================
class Aluno(models.Model):
    igreja = models.ForeignKey(Igreja, on_delete=models.PROTECT, related_name="alunos")
    nome = models.CharField(max_length=200)
    data_nascimento = models.DateField()

    class Meta:
        verbose_name = "Aluno"
        verbose_name_plural = "Alunos"
        ordering = ["nome"]

    def __str__(self):
        return self.nome



# MATRÍCULA
# ==================
class Matricula(models.Model):
    aluno = models.ForeignKey(Aluno, on_delete=models.PROTECT, related_name="matriculas")
    trimestre = models.ForeignKey(Trimestre, on_delete=models.PROTECT, related_name="matriculas")
    classe = models.ForeignKey(Classe, on_delete=models.PROTECT, related_name="matriculas")
    data_matricula = models.DateField(default=timezone.now)
    ativa = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Matrícula"
        verbose_name_plural = "Matrículas"
        unique_together = ('aluno', 'trimestre', 'classe')

    def __str__(self):
        return f"{self.aluno.nome} - {self.classe.nome}"



# DIÁRIO
# ==================
class Diario(models.Model):
    aula = models.OneToOneField(Aula, on_delete=models.CASCADE, related_name="diario")
    data_da_aula = models.DateField(default=timezone.now)
    alunos_presentes = models.PositiveIntegerField(default=0)
    alunos_ausentes = models.PositiveIntegerField(default=0)
    visitantes = models.PositiveIntegerField(default=0)
    biblias = models.PositiveIntegerField(default=0)
    ofertas = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    dizimos = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    observacoes = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name = "Diário"
        verbose_name_plural = "Diários"

    def __str__(self):
        return f"Diário: {self.aula.titulo} ({self.data_da_aula})"



# PRESENÇA
# ==================
class Presenca(models.Model):
    PRESENCA_CHOICES = [
        ('P', 'Presente'),
        ('F', 'Ausente'),
    ]
    aluno = models.ForeignKey(Aluno, on_delete=models.PROTECT, related_name="presencas")
    diario = models.ForeignKey(Diario, on_delete=models.CASCADE, related_name="presencas")
    status = models.CharField(max_length=8, choices=PRESENCA_CHOICES, default='F') #Chamada

    class Meta:
        verbose_name = "Presença"
        verbose_name_plural = "Presenças"
        unique_together = ('aluno', 'diario')

    def __str__(self):
        return f"{self.aluno.nome} - {self.get_status_display()}"

# Create your models here.
