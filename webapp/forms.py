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

