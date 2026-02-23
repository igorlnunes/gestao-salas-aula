from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("webapp", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="PerfilUsuario",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "nome_completo",
                    models.CharField("Nome completo", max_length=255),
                ),
                (
                    "endereco",
                    models.CharField("Endereço", max_length=255, blank=True),
                ),
                (
                    "user",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="perfil",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="Usuário",
                    ),
                ),
            ],
            options={
                "verbose_name": "Perfil de usuário",
                "verbose_name_plural": "Perfis de usuários",
            },
        ),
    ]

