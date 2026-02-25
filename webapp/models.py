from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models


class Sala(models.Model):
    """Sala de aula com nome e faixa de horários em que fica disponível."""

    TIPO_CHOICES = [
        ("laboratorio", "Laboratório"),
        ("auditorio", "Auditório"),
        ("comum", "Sala Comum"),
        ("outro", "Outro"),
    ]

    nome = models.CharField("Nome da sala", max_length=100, unique=True)
    capacidade = models.PositiveIntegerField("Capacidade máxima", default=30)
    hora_inicio = models.TimeField("Horário de início")
    hora_fim = models.TimeField("Horário de término")

    class Meta:
        verbose_name = "Sala"
        verbose_name_plural = "Salas"
        ordering = ["nome"]

    def __str__(self):
        return self.nome

    def clean(self):
        super().clean()
        if self.hora_inicio and self.hora_fim and self.hora_fim <= self.hora_inicio:
            raise ValidationError(
                {"hora_fim": "O horário de término da sala deve ser sempre posterior ao de início."}
            )


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
    quantidade_pessoas = models.PositiveIntegerField("Quantidade de pessoas", default=1)

    class Meta:
        verbose_name = "Reserva"
        verbose_name_plural = "Reservas"
        ordering = ["-data_hora_inicio"]

    def __str__(self):
        return f"{self.sala.nome} — {self.data_hora_inicio} a {self.data_hora_fim}"

    def clean(self):
        super().clean()
        try:
            if self.sala and self.quantidade_pessoas:
                if self.quantidade_pessoas > self.sala.capacidade:
                    raise ValidationError(
                        {"quantidade_pessoas": f"A quantidade reservada ({self.quantidade_pessoas}) excede a capacidade da sala ({self.sala.capacidade} pessoas)."}
                    )
        except Sala.DoesNotExist:
            pass


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
