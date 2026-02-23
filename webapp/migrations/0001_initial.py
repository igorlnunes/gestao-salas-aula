# Generated manually for Sala and Reserva

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Sala",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("nome", models.CharField(max_length=100, verbose_name="Nome da sala")),
                ("hora_inicio", models.TimeField(verbose_name="Horário de início")),
                ("hora_fim", models.TimeField(verbose_name="Horário de término")),
            ],
            options={
                "verbose_name": "Sala",
                "verbose_name_plural": "Salas",
                "ordering": ["nome"],
            },
        ),
        migrations.CreateModel(
            name="Reserva",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("data_hora_inicio", models.DateTimeField(verbose_name="Início")),
                ("data_hora_fim", models.DateTimeField(verbose_name="Término")),
                (
                    "sala",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="reservas",
                        to="webapp.sala",
                    ),
                ),
                (
                    "usuario",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="reservas",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "verbose_name": "Reserva",
                "verbose_name_plural": "Reservas",
                "ordering": ["-data_hora_inicio"],
            },
        ),
    ]
