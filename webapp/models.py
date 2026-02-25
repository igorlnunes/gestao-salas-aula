from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone


class Sala(models.Model):
    """Sala de aula com nome e faixa de horários em que fica disponível."""

    TIPO_CHOICES = [
        ("laboratorio", "Laboratório"),
        ("auditorio", "Auditório"),
        ("comum", "Sala Comum"),
        ("outro", "Outro"),
    ]

    nome = models.CharField("Nome da sala", max_length=100, unique=True)
    tipo = models.CharField("Tipo de sala", max_length=20, choices=TIPO_CHOICES, default="comum")
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
        # RN-08 — não é permitido reservar com data/hora no passado
        if self.data_hora_inicio and self.data_hora_inicio < timezone.now():
            raise ValidationError(
                {"data_hora_inicio": "Não é permitido fazer reservas com data/hora no passado."}
            )
        # RN-05 — início da reserva deve ser anterior ao término
        if self.data_hora_inicio and self.data_hora_fim:
            if self.data_hora_fim <= self.data_hora_inicio:
                raise ValidationError(
                    {"data_hora_fim": "O horário de término da reserva deve ser posterior ao de início."}
                )
            # RN-09 — duração mínima de 30 minutos e máxima de 4 horas
            from datetime import timedelta
            duracao = self.data_hora_fim - self.data_hora_inicio
            if duracao < timedelta(minutes=30):
                raise ValidationError(
                    {"data_hora_fim": "A reserva deve ter duração mínima de 30 minutos."}
                )
            if duracao > timedelta(hours=4):
                raise ValidationError(
                    {"data_hora_fim": "A reserva não pode ter duração superior a 4 horas."}
                )
        # RN-03 — quantidade de pessoas não pode exceder capacidade da sala
        try:
            if self.sala and self.quantidade_pessoas:
                if self.quantidade_pessoas > self.sala.capacidade:
                    raise ValidationError(
                        {"quantidade_pessoas": f"A quantidade reservada ({self.quantidade_pessoas}) excede a capacidade da sala ({self.sala.capacidade} pessoas)."}
                    )
        except Sala.DoesNotExist:
            pass
        # RN-06 — não é permitido fazer reservas sobrepostas para a mesma sala
        if self.sala_id and self.data_hora_inicio and self.data_hora_fim:
            conflitos = Reserva.objects.filter(
                sala=self.sala_id,
                data_hora_inicio__lt=self.data_hora_fim,
                data_hora_fim__gt=self.data_hora_inicio,
            )
            if self.pk:
                conflitos = conflitos.exclude(pk=self.pk)
            if conflitos.exists():
                raise ValidationError(
                    "Já existe uma reserva para esta sala nesse período. Escolha outro horário."
                )
        # RN-07 — reserva deve estar dentro do horário de disponibilidade da sala
        try:
            if self.sala and self.data_hora_inicio and self.data_hora_fim:
                hora_reserva_inicio = self.data_hora_inicio.time()
                hora_reserva_fim = self.data_hora_fim.time()
                if hora_reserva_inicio < self.sala.hora_inicio:
                    raise ValidationError(
                        {"data_hora_inicio": f"A reserva não pode começar antes do horário de abertura da sala ({self.sala.hora_inicio.strftime('%H:%M')})."}
                    )
                if hora_reserva_fim > self.sala.hora_fim:
                    raise ValidationError(
                        {"data_hora_fim": f"A reserva não pode terminar após o horário de encerramento da sala ({self.sala.hora_fim.strftime('%H:%M')})."}
                    )
        except Sala.DoesNotExist:
            pass
        # RN-10 — um usuário não pode ter mais de 3 reservas ativas simultaneamente
        MAX_RESERVAS_ATIVAS = 3
        if self.usuario_id and self.data_hora_fim:
            reservas_ativas = Reserva.objects.filter(
                usuario=self.usuario_id,
                data_hora_fim__gt=timezone.now(),
            )
            if self.pk:
                reservas_ativas = reservas_ativas.exclude(pk=self.pk)
            if reservas_ativas.count() >= MAX_RESERVAS_ATIVAS:
                raise ValidationError(
                    f"Você já possui {MAX_RESERVAS_ATIVAS} reservas ativas. "
                    "Cancele uma reserva existente antes de criar uma nova."
                )


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
