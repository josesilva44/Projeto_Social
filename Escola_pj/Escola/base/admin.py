# base/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Usuario, Igreja, Classe, Professor, Aula, Trimestre


class ProfessorInline(admin.StackedInline):
    """Permite vincular o perfil de Professor a classe."""
    model = Professor
    fk_name = 'usuario'
    can_delete = False
    verbose_name = 'Perfil de Professor'
    verbose_name_plural = 'Perfil de Professor'
    extra = 1
    max_num = 1

class UsuarioAdmin(UserAdmin):
    model = Usuario
    list_display = ("username", "email", "role", "igreja", "is_staff", "is_active")
    list_filter = ("role", "is_staff", "is_active")

    inlines = (ProfessorInline,)

    # Campos de edição
    fieldsets = (
        (None, {"fields": ("username", "password")}),
        ("Informações pessoais", {"fields": ("first_name", "last_name", "email", "igreja", "role")}),
        ("Permissões", {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),
        ("Datas importantes", {"fields": ("last_login", "date_joined")}),
    )

    # Campos de criação
    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("username", "email", "igreja", "role", "password1", "password2", "is_active", "is_staff"),
        }),
    )

    search_fields = ("username", "email")
    ordering = ("username",)

admin.site.register(Usuario, UsuarioAdmin)
admin.site.register(Igreja)
admin.site.register(Classe)
admin.site.register(Professor)
admin.site.register(Aula)
admin.site.register(Trimestre)
