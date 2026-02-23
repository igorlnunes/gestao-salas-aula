from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView, LogoutView
from django.utils import timezone
from django.views.generic import CreateView
from django.urls import reverse_lazy

from .forms import RegistroForm, SalaForm
from .models import Sala, Reserva


@login_required
def welcome(request):
    return redirect("dashboard")


@login_required
def dashboard(request):
    """Lista salas disponíveis e ocupadas no momento."""
    now = timezone.now()
    reservas_agora = Reserva.objects.filter(
        data_hora_inicio__lte=now,
        data_hora_fim__gte=now,
    )
    salas_ocupadas_ids = reservas_agora.values_list("sala_id", flat=True)
    salas_ocupadas = Sala.objects.filter(id__in=salas_ocupadas_ids)
    salas_disponiveis = Sala.objects.exclude(id__in=salas_ocupadas_ids)

    reservas_ativas = {r.sala_id: r for r in reservas_agora.select_related("sala", "usuario")}
    ocupadas_com_reserva = [(sala, reservas_ativas.get(sala.id)) for sala in salas_ocupadas]

    return render(
        request,
        "webapp/dashboard.html",
        {
            "salas_disponiveis": salas_disponiveis,
            "salas_ocupadas": salas_ocupadas,
            "ocupadas_com_reserva": ocupadas_com_reserva,
            "agora": now,
        },
    )


class SalaCreateView(CreateView):
    form_class = SalaForm
    template_name = "webapp/sala_form.html"
    success_url = reverse_lazy("dashboard")

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect("login")
        return super().dispatch(request, *args, **kwargs)


class LoginViewCustom(LoginView):
    template_name = "webapp/login.html"
    redirect_authenticated_user = True


class LogoutViewCustom(LogoutView):
    next_page = "login"


class RegistroView(CreateView):
    form_class = RegistroForm
    template_name = "webapp/register.html"
    success_url = reverse_lazy("welcome")

    def form_valid(self, form):
        user = form.save()
        login(self.request, user)
        return redirect(self.success_url)
