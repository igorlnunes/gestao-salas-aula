from django import forms
from django.contrib.auth.models import User
from django.utils import timezone

from .models import Sala, Reserva, PerfilUsuario


class RegistroForm(forms.ModelForm):
    """Formulário de cadastro com dados pessoais básicos."""

    nome_completo = forms.CharField(
        label="Nome completo",
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "autocomplete": "name",
            }
        ),
    )
    email = forms.EmailField(
        label="E-mail",
        widget=forms.EmailInput(
            attrs={
                "class": "form-control",
                "autocomplete": "email",
            }
        ),
    )
    endereco = forms.CharField(
        label="Endereço (opcional)",
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "autocomplete": "street-address",
            }
        ),
    )
    password = forms.CharField(
        label="Senha",
        widget=forms.PasswordInput(
            attrs={
                "class": "form-control",
                "autocomplete": "new-password",
            }
        ),
        min_length=8,
    )
    password_confirm = forms.CharField(
        label="Confirmar senha",
        widget=forms.PasswordInput(
            attrs={
                "class": "form-control",
                "autocomplete": "new-password",
            }
        ),
    )

    class Meta:
        model = User
        fields = ("username",)
        labels = {"username": "Usuário"}
        widgets = {
            "username": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "autocomplete": "username",
                }
            )
        }

    def clean_username(self):
        username = self.cleaned_data.get("username")
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError("Este nome de usuário já está em uso.")
        return username

    def clean_email(self):
        email = self.cleaned_data.get("email")
        if email and User.objects.filter(email=email).exists():
            raise forms.ValidationError("Este e-mail já está em uso.")
        return email

    def clean(self):
        data = super().clean()
        password = data.get("password")
        password_confirm = data.get("password_confirm")
        if password and password_confirm and password != password_confirm:
            raise forms.ValidationError({"password_confirm": "As senhas não coincidem."})
        return data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data.get("email")
        # Armazena o nome completo em first_name para manter simples
        user.first_name = self.cleaned_data.get("nome_completo", "")
        user.set_password(self.cleaned_data["password"])

        if commit:
            user.save()
            PerfilUsuario.objects.create(
                user=user,
                nome_completo=self.cleaned_data.get("nome_completo", ""),
                endereco=self.cleaned_data.get("endereco", ""),
            )
        return user


class SalaForm(forms.ModelForm):
    """Formulário para criar/editar sala: nome e faixa de horários."""

    class Meta:
        model = Sala
        fields = ("nome", "tipo", "capacidade", "hora_inicio", "hora_fim")
        labels = {
            "nome": "Nome da sala",
            "tipo": "Tipo de sala",
            "capacidade": "Capacidade (pessoas)",
            "hora_inicio": "Horário de início",
            "hora_fim": "Horário de término",
        }
        widgets = {
            "nome": forms.TextInput(attrs={"class": "form-control", "placeholder": "Ex: Sala 101"}),
            "tipo": forms.Select(attrs={"class": "form-select"}),
            "capacidade": forms.NumberInput(attrs={"class": "form-control", "min": "1"}),
            "hora_inicio": forms.TimeInput(attrs={"class": "form-control", "type": "time"}),
            "hora_fim": forms.TimeInput(attrs={"class": "form-control", "type": "time"}),
        }

    def clean(self):
        data = super().clean()
        inicio = data.get("hora_inicio")
        fim = data.get("hora_fim")
        if inicio and fim and inicio >= fim:
            raise forms.ValidationError("O horário de término deve ser posterior ao de início.")
        return data


class ReservaForm(forms.ModelForm):
    """Formulário para criar uma reserva de sala."""

    class Meta:
        model = Reserva
        fields = ("sala", "data_hora_inicio", "data_hora_fim", "quantidade_pessoas")
        labels = {
            "sala": "Sala",
            "data_hora_inicio": "Data e hora de início",
            "data_hora_fim": "Data e hora de término",
            "quantidade_pessoas": "Quantidade de pessoas",
        }
        widgets = {
            "sala": forms.Select(attrs={"class": "form-select"}),
            "data_hora_inicio": forms.DateTimeInput(
                attrs={"class": "form-control", "type": "datetime-local"},
                format="%Y-%m-%dT%H:%M",
            ),
            "data_hora_fim": forms.DateTimeInput(
                attrs={"class": "form-control", "type": "datetime-local"},
                format="%Y-%m-%dT%H:%M",
            ),
            "quantidade_pessoas": forms.NumberInput(attrs={"class": "form-control", "min": "1"}),
        }

    def __init__(self, *args, **kwargs):
        self.usuario = kwargs.pop("usuario", None)
        super().__init__(*args, **kwargs)
        # Garante que os campos datetime-local aceitem o formato correto
        self.fields["data_hora_inicio"].input_formats = ["%Y-%m-%dT%H:%M"]
        self.fields["data_hora_fim"].input_formats = ["%Y-%m-%dT%H:%M"]

    def clean(self):
        data = super().clean()
        inicio = data.get("data_hora_inicio")
        fim = data.get("data_hora_fim")
        sala = data.get("sala")
        agora = timezone.now()
        # RN-08 — não é permitido reservar com data/hora no passado
        if inicio and inicio < agora:
            raise forms.ValidationError(
                {"data_hora_inicio": "Não é permitido fazer reservas com data/hora no passado."}
            )

        # RN-14 — antecedência mínima de 15 minutos para fazer uma reserva
        from datetime import timedelta
        if not self.instance.pk and inicio:
            if inicio < agora + timedelta(minutes=15):
                raise forms.ValidationError(
                    {"data_hora_inicio": "A reserva deve ser feita com pelo menos 15 minutos de antecedência."}
                )
        # RN-05 — início da reserva deve ser anterior ao término
        if inicio and fim and fim <= inicio:
            raise forms.ValidationError(
                {"data_hora_fim": "O horário de término da reserva deve ser posterior ao de início."}
            )
        # RN-09 — duração mínima de 30 minutos e máxima de 4 horas
        if inicio and fim and fim > inicio:
            from datetime import timedelta
            duracao = fim - inicio
            if duracao < timedelta(minutes=30):
                raise forms.ValidationError(
                    {"data_hora_fim": "A reserva deve ter duração mínima de 30 minutos."}
                )
            if duracao > timedelta(hours=4):
                raise forms.ValidationError(
                    {"data_hora_fim": "A reserva não pode ter duração superior a 4 horas."}
                )
        # RN-06 — não é permitido fazer reservas sobrepostas para a mesma sala
        if sala and inicio and fim:
            conflitos = Reserva.objects.filter(
                sala=sala,
                data_hora_inicio__lt=fim,
                data_hora_fim__gt=inicio,
            )
            if self.instance and self.instance.pk:
                conflitos = conflitos.exclude(pk=self.instance.pk)
            if conflitos.exists():
                raise forms.ValidationError(
                    "Já existe uma reserva para esta sala nesse período. Escolha outro horário."
                )
        # RN-07 — reserva deve estar dentro do horário de disponibilidade da sala
        if sala and inicio and fim:
            hora_inicio_reserva = inicio.time()
            hora_fim_reserva = fim.time()
            if hora_inicio_reserva < sala.hora_inicio:
                raise forms.ValidationError(
                    {"data_hora_inicio": f"A reserva não pode começar antes do horário de abertura da sala ({sala.hora_inicio.strftime('%H:%M')})."}
                )
            if hora_fim_reserva > sala.hora_fim:
                raise forms.ValidationError(
                    {"data_hora_fim": f"A reserva não pode terminar após o horário de encerramento da sala ({sala.hora_fim.strftime('%H:%M')})."}
                )
        # RN-10 — um usuário não pode ter mais de 3 reservas ativas simultaneamente
        MAX_RESERVAS_ATIVAS = 3
        if self.usuario and self.usuario.is_authenticated:
            from django.utils import timezone as tz
            reservas_ativas = Reserva.objects.filter(
                usuario=self.usuario,
                data_hora_fim__gt=tz.now(),
            )
            if self.instance and self.instance.pk:
                reservas_ativas = reservas_ativas.exclude(pk=self.instance.pk)
            if reservas_ativas.count() >= MAX_RESERVAS_ATIVAS:
                raise forms.ValidationError(
                    f"Você já possui {MAX_RESERVAS_ATIVAS} reservas ativas. "
                    "Cancele uma reserva existente antes de criar uma nova."
                )
        return data


class ReservaRecorrenteForm(forms.Form):
    """RN-22 e RN-23 — Formulário para criar reservas recorrentes semanais."""

    DIAS_SEMANA_CHOICES = [
        (0, "Segunda-feira"),
        (1, "Terça-feira"),
        (2, "Quarta-feira"),
        (3, "Quinta-feira"),
        (4, "Sexta-feira"),
        (5, "Sábado"),
        (6, "Domingo"),
    ]

    MAX_SEMANAS = 12

    sala = forms.ModelChoiceField(
        queryset=Sala.objects.all(),
        label="Sala",
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    dia_da_semana = forms.ChoiceField(
        choices=DIAS_SEMANA_CHOICES,
        label="Dia da semana",
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    hora_inicio = forms.TimeField(
        label="Hora de início",
        widget=forms.TimeInput(attrs={"class": "form-control", "type": "time"}),
    )
    hora_fim = forms.TimeField(
        label="Hora de término",
        widget=forms.TimeInput(attrs={"class": "form-control", "type": "time"}),
    )
    data_inicio_recorrencia = forms.DateField(
        label="A partir de (data)",
        widget=forms.DateInput(attrs={"class": "form-control", "type": "date"}),
        help_text="Primeira data a partir da qual as reservas serão geradas.",
    )
    num_semanas = forms.IntegerField(
        label="Número de semanas",
        min_value=1,
        max_value=MAX_SEMANAS,
        initial=4,
        widget=forms.NumberInput(attrs={"class": "form-control", "min": "1", "max": str(MAX_SEMANAS)}),
        help_text=f"Máximo de {MAX_SEMANAS} semanas.",
    )
    quantidade_pessoas = forms.IntegerField(
        label="Quantidade de pessoas",
        min_value=1,
        initial=1,
        widget=forms.NumberInput(attrs={"class": "form-control", "min": "1"}),
    )

    def __init__(self, *args, **kwargs):
        self.usuario = kwargs.pop("usuario", None)
        super().__init__(*args, **kwargs)

    def _gerar_datas(self, data_inicio, dia_semana, num_semanas):
        """Gera as datas das ocorrências recorrentes."""
        from datetime import date, timedelta
        datas = []
        # Encontra a primeira data a partir de data_inicio com o dia da semana desejado
        delta_dias = (dia_semana - data_inicio.weekday()) % 7
        primeira_data = data_inicio + timedelta(days=delta_dias)
        for i in range(num_semanas):
            datas.append(primeira_data + timedelta(weeks=i))
        return datas

    def clean(self):
        from datetime import timedelta, datetime
        from django.utils import timezone as tz

        data = super().clean()
        sala = data.get("sala")
        hora_inicio = data.get("hora_inicio")
        hora_fim = data.get("hora_fim")
        data_inicio_recorrencia = data.get("data_inicio_recorrencia")
        num_semanas = data.get("num_semanas")
        quantidade_pessoas = data.get("quantidade_pessoas")
        dia_semana = data.get("dia_da_semana")

        if not all([sala, hora_inicio, hora_fim, data_inicio_recorrencia, num_semanas, dia_semana is not None]):
            return data

        dia_semana = int(dia_semana)

        # RN-05 — início antes do término
        if hora_fim <= hora_inicio:
            raise forms.ValidationError(
                {"hora_fim": "O horário de término deve ser posterior ao de início."}
            )

        # RN-09 — duração mínima 30 min, máxima 4 horas
        from datetime import date as _date
        dt_inicio_base = datetime.combine(_date.today(), hora_inicio)
        dt_fim_base = datetime.combine(_date.today(), hora_fim)
        duracao = dt_fim_base - dt_inicio_base
        if duracao < timedelta(minutes=30):
            raise forms.ValidationError(
                {"hora_fim": "A reserva deve ter duração mínima de 30 minutos."}
            )
        if duracao > timedelta(hours=4):
            raise forms.ValidationError(
                {"hora_fim": "A reserva não pode ter duração superior a 4 horas."}
            )

        # RN-07 — dentro do horário de disponibilidade da sala
        if hora_inicio < sala.hora_inicio:
            raise forms.ValidationError(
                {"hora_inicio": f"A reserva não pode começar antes da abertura da sala ({sala.hora_inicio.strftime('%H:%M')})."}
            )
        if hora_fim > sala.hora_fim:
            raise forms.ValidationError(
                {"hora_fim": f"A reserva não pode terminar após o encerramento da sala ({sala.hora_fim.strftime('%H:%M')})."}
            )

        # RN-03 — capacidade
        if quantidade_pessoas and quantidade_pessoas > sala.capacidade:
            raise forms.ValidationError(
                {"quantidade_pessoas": f"A quantidade reservada ({quantidade_pessoas}) excede a capacidade da sala ({sala.capacidade} pessoas)."}
            )

        # RN-08 — primeira data não pode estar no passado
        hoje = tz.localdate()
        if data_inicio_recorrencia < hoje:
            raise forms.ValidationError(
                {"data_inicio_recorrencia": "A data de início não pode estar no passado."}
            )

        # RN-22 — limite máximo de semanas
        if num_semanas > self.MAX_SEMANAS:
            raise forms.ValidationError(
                {"num_semanas": f"O número máximo de semanas é {self.MAX_SEMANAS}."}
            )

        # Gera as datas das ocorrências
        datas = self._gerar_datas(data_inicio_recorrencia, dia_semana, num_semanas)
        self.cleaned_data["_datas_ocorrencias"] = datas

        # RN-23 — verifica disponibilidade em TODAS as datas antes de confirmar
        conflitos = []
        for dt in datas:
            dt_inicio = tz.make_aware(datetime.combine(dt, hora_inicio))
            dt_fim = tz.make_aware(datetime.combine(dt, hora_fim))

            # RN-08 — ignora datas no passado (primeira data pode ser hoje mas hora já passou)
            if dt_inicio < tz.now():
                conflitos.append(f"{dt.strftime('%d/%m/%Y')} (horário no passado)")
                continue

            qs_conflito = Reserva.objects.filter(
                sala=sala,
                data_hora_inicio__lt=dt_fim,
                data_hora_fim__gt=dt_inicio,
            )
            if qs_conflito.exists():
                conflitos.append(dt.strftime("%d/%m/%Y"))

        if conflitos:
            raise forms.ValidationError(
                f"Conflito de horário nas seguintes datas: {', '.join(conflitos)}. "
                "Escolha outro horário ou reduza o número de semanas."
            )

        return data

    def criar_reservas(self, usuario):
        """Cria todas as reservas recorrentes validadas. Retorna a lista de reservas criadas."""
        from datetime import datetime
        from django.utils import timezone as tz

        datas = self.cleaned_data["_datas_ocorrencias"]
        sala = self.cleaned_data["sala"]
        hora_inicio = self.cleaned_data["hora_inicio"]
        hora_fim = self.cleaned_data["hora_fim"]
        quantidade_pessoas = self.cleaned_data["quantidade_pessoas"]

        reservas_criadas = []
        for dt in datas:
            dt_inicio = tz.make_aware(datetime.combine(dt, hora_inicio))
            dt_fim = tz.make_aware(datetime.combine(dt, hora_fim))
            reserva = Reserva.objects.create(
                sala=sala,
                usuario=usuario,
                data_hora_inicio=dt_inicio,
                data_hora_fim=dt_fim,
                quantidade_pessoas=quantidade_pessoas,
            )
            reservas_criadas.append(reserva)
        return reservas_criadas
