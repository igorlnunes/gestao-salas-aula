from django import forms
from django.contrib.auth.models import User

from .models import Sala, PerfilUsuario


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
        fields = ("nome", "capacidade", "hora_inicio", "hora_fim")
        labels = {
            "nome": "Nome da sala",
            "capacidade": "Capacidade máxima",
            "hora_inicio": "Horário de início",
            "hora_fim": "Horário de término",
        }
        widgets = {
            "nome": forms.TextInput(attrs={"class": "form-control", "placeholder": "Ex: Sala 101"}),
            "capacidade": forms.NumberInput(attrs={"class": "form-control", "min": 1}),
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
