from django.conf import settings
from django.db import models


class Sala(models.Model):
    """Sala de aula com nome e faixa de horários em que fica disponível."""

    nome = models.CharField("Nome da sala", max_length=100)
    hora_inicio = models.TimeField("Horário de início")
    hora_fim = models.TimeField("Horário de término")

    class Meta:
        verbose_name = "Sala"
        verbose_name_plural = "Salas"
        ordering = ["nome"]

    def __str__(self):
        return self.nome


class Reserva(models.Model):
    """Reserva de uma sala em um período (define quando a sala está ocupada)."""

    sala = models.ForeignKey(Sala, on_delete=models.CASCADE, related_name="reservas")
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="reservas",
        null=True,
        blank=True,
    )
    data_hora_inicio = models.DateTimeField("Início")
    data_hora_fim = models.DateTimeField("Término")

    class Meta:
        verbose_name = "Reserva"
        verbose_name_plural = "Reservas"
        ordering = ["-data_hora_inicio"]

    def __str__(self):
        return f"{self.sala.nome} — {self.data_hora_inicio} a {self.data_hora_fim}"


class PerfilUsuario(models.Model):
    """Informações adicionais do usuário cadastradas no fluxo de registro."""

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="perfil",
        verbose_name="Usuário",
    )
    nome_completo = models.CharField("Nome completo", max_length=255)
    endereco = models.CharField("Endereço", max_length=255, blank=True)

    class Meta:
        verbose_name = "Perfil de usuário"
        verbose_name_plural = "Perfis de usuários"

    def __str__(self):
        return self.nome_completo
