from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView, LogoutView
from django.utils import timezone
from django.contrib import messages
from django.views.generic import CreateView, DeleteView, View
from django.urls import reverse_lazy
from django.shortcuts import get_object_or_404
from datetime import timedelta

from .forms import RegistroForm, SalaForm, ReservaForm
from .models import Sala, Reserva


def welcome(request):
    return render(request, "webapp/welcome.html")


@login_required
def dashboard(request):
    """Lista salas disponíveis e ocupadas no momento."""
    now = timezone.now()
    
    # RN-12: Reservas onde data_hora_inicio <= now - 15 e check_in_realizado=False são ignoradas
    limite_checkin = now - timedelta(minutes=15)
    
    reservas_agora = Reserva.objects.filter(
        data_hora_inicio__lte=now,
        data_hora_fim__gte=now,
    ).exclude(
        data_hora_inicio__lte=limite_checkin,
        check_in_realizado=False
    )
    
    salas_ocupadas_ids = reservas_agora.values_list("sala_id", flat=True)
    salas_ocupadas = Sala.objects.filter(id__in=salas_ocupadas_ids)
    salas_disponiveis = Sala.objects.exclude(id__in=salas_ocupadas_ids)

    reservas_ativas = {r.sala_id: r for r in reservas_agora.select_related("sala", "usuario")}
    ocupadas_com_reserva = [(sala, reservas_ativas.get(sala.id)) for sala in salas_ocupadas]

    # Minhas reservas (futuras e ativas)
    minhas_reservas = Reserva.objects.filter(
        usuario=request.user,
        data_hora_fim__gte=now
    ).order_by("data_hora_inicio")

    # RN-13: Notificação de reserva em menos de 2 horas
    limite_notificacao = now + timedelta(hours=2)
    reservas_proximas = minhas_reservas.filter(
        data_hora_inicio__gt=now,
        data_hora_inicio__lte=limite_notificacao
    )
    for res in reservas_proximas:
        messages.info(request, f"Lembrete: Sua reserva para a sala {res.sala.nome} começará às {res.data_hora_inicio.strftime('%H:%M')}.")

    return render(
        request,
        "webapp/dashboard.html",
        {
            "salas_disponiveis": salas_disponiveis,
            "salas_ocupadas": salas_ocupadas,
            "ocupadas_com_reserva": ocupadas_com_reserva,
            "minhas_reservas": minhas_reservas,
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


class ReservaCreateView(CreateView):
    form_class = ReservaForm
    template_name = "webapp/reserva_form.html"
    success_url = reverse_lazy("dashboard")

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect("login")
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["usuario"] = self.request.user
        return kwargs

    def form_valid(self, form):
        reserva = form.save(commit=False)
        reserva.usuario = self.request.user
        reserva.save()
        messages.success(self.request, "Reserva criada com sucesso.")
        return redirect(self.success_url)


class ReservaDeleteView(DeleteView):
    model = Reserva
    success_url = reverse_lazy("dashboard")

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect("login")
        reserva = self.get_object()
        if reserva.usuario != request.user:
            messages.error(request, "Você só pode cancelar suas próprias reservas.")
            return redirect("dashboard")
        
        # RN-11: Antecedência mínima de 1 hora para cancelamento
        if timezone.now() > reserva.data_hora_inicio - timedelta(hours=1):
            messages.error(request, "A reserva só pode ser cancelada com pelo menos 1 hora de antecedência.")
            return redirect("dashboard")
            
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        return self.post(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        messages.success(request, "Reserva cancelada com sucesso.")
        return super().delete(request, *args, **kwargs)


class ReservaCheckInView(View):
    def post(self, request, pk, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect("login")
            
        reserva = get_object_or_404(Reserva, pk=pk)
        
        if reserva.usuario != request.user:
            messages.error(request, "Você não tem permissão para fazer check-in nesta reserva.")
            return redirect("dashboard")
            
        reserva.check_in_realizado = True
        reserva.save()
        messages.success(request, f"Check-in realizado com sucesso para a sala {reserva.sala.nome}.")
        return redirect("dashboard")


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
