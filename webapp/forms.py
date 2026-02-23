from django import forms
from django.contrib.auth.models import User

from .models import Sala


class RegistroForm(forms.ModelForm):
    """Formulário de cadastro: apenas usuário e senha."""

    password = forms.CharField(
        label="Senha",
        widget=forms.PasswordInput(attrs={"class": "form-control", "autocomplete": "new-password"}),
        min_length=8,
    )
    password_confirm = forms.CharField(
        label="Confirmar senha",
        widget=forms.PasswordInput(attrs={"class": "form-control", "autocomplete": "new-password"}),
    )

    class Meta:
        model = User
        fields = ("username",)
        labels = {"username": "Usuário"}
        widgets = {"username": forms.TextInput(attrs={"class": "form-control", "autocomplete": "username"})}

    def clean_username(self):
        username = self.cleaned_data.get("username")
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError("Este nome de usuário já está em uso.")
        return username

    def clean(self):
        data = super().clean()
        password = data.get("password")
        password_confirm = data.get("password_confirm")
        if password and password_confirm and password != password_confirm:
            raise forms.ValidationError({"password_confirm": "As senhas não coincidem."})
        return data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password"])
        if commit:
            user.save()
        return user


class SalaForm(forms.ModelForm):
    """Formulário para criar/editar sala: nome e faixa de horários."""

    class Meta:
        model = Sala
        fields = ("nome", "hora_inicio", "hora_fim")
        labels = {
            "nome": "Nome da sala",
            "hora_inicio": "Horário de início",
            "hora_fim": "Horário de término",
        }
        widgets = {
            "nome": forms.TextInput(attrs={"class": "form-control", "placeholder": "Ex: Sala 101"}),
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
