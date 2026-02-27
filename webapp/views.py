from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView, LogoutView
from django.utils import timezone
from django.contrib import messages
from django.views.generic import CreateView, DeleteView, View, UpdateView, ListView
from django.contrib.auth.mixins import UserPassesTestMixin
from django.urls import reverse_lazy
from django.shortcuts import get_object_or_404
from datetime import timedelta, datetime, date
from django.db.models import Sum, ExpressionWrapper, F, DurationField

from .forms import RegistroForm, SalaForm, ReservaForm, ReservaRecorrenteForm
from .models import Sala, Reserva


# -------------------------
# Helpers para RN-19 / RN-20
# -------------------------

def _calcular_taxa_ocupacao(sala, data_inicio, data_fim):
    """
    Calcula a taxa de ocupação de uma sala em um intervalo de datas.
    Retorna um valor entre 0 e 100 (percentual).
    """
    # Janela total de disponibilidade da sala no intervalo (em minutos)
    from datetime import datetime as dt
    import math

    # Número de dias no intervalo
    delta = data_fim - data_inicio
    num_dias = max(delta.days, 1)

    # Minutos disponíveis por dia
    sala_inicio_dt = dt.combine(date.today(), sala.hora_inicio)
    sala_fim_dt = dt.combine(date.today(), sala.hora_fim)
    minutos_disponiveis_dia = (sala_fim_dt - sala_inicio_dt).total_seconds() / 60
    total_minutos_disponiveis = minutos_disponiveis_dia * num_dias

    if total_minutos_disponiveis <= 0:
        return 0

    # Reservas no período
    reservas = Reserva.objects.filter(
        sala=sala,
        data_hora_inicio__lt=data_fim,
        data_hora_fim__gt=data_inicio,
    )

    total_minutos_reservados = 0
    for r in reservas:
        inicio_efetivo = max(r.data_hora_inicio, data_inicio)
        fim_efetivo = min(r.data_hora_fim, data_fim)
        if fim_efetivo > inicio_efetivo:
            total_minutos_reservados += (fim_efetivo - inicio_efetivo).total_seconds() / 60

    taxa = (total_minutos_reservados / total_minutos_disponiveis) * 100
    return min(round(taxa, 1), 100)


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

    # Reservas (futuras e ativas)
    if request.user.is_staff:
        minhas_reservas = Reserva.objects.filter(data_hora_fim__gte=now).order_by("data_hora_inicio")
    else:
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

    # RN-19: Taxa de ocupação de cada sala (hoje) — anota o atributo diretamente no objeto
    hoje_inicio = now.replace(hour=0, minute=0, second=0, microsecond=0)
    hoje_fim = hoje_inicio + timedelta(days=1)
    todas_as_salas = list(Sala.objects.all())
    for sala_obj in todas_as_salas:
        sala_obj.taxa_ocupacao = _calcular_taxa_ocupacao(sala_obj, hoje_inicio, hoje_fim)

    # Reconstroi as querysets anotadas
    sala_map = {s.id: s for s in todas_as_salas}
    salas_disponiveis_anotadas = [sala_map[sid] for sid in
        Sala.objects.exclude(id__in=salas_ocupadas_ids).values_list('id', flat=True)
        if sid in sala_map]
    salas_ocupadas_anotadas = [sala_map[sid] for sid in
        Sala.objects.filter(id__in=salas_ocupadas_ids).values_list('id', flat=True)
        if sid in sala_map]
    ocupadas_com_reserva_anotadas = [
        (sala_map.get(sala.id, sala), reserva)
        for sala, reserva in ocupadas_com_reserva
    ]

    # RN-20: Salas com baixa utilização na semana (< 20%) — apenas para admins
    LIMIAR_BAIXA_UTILIZACAO = 20  # percentual
    salas_baixa_utilizacao = []
    if request.user.is_staff:
        semana_inicio = hoje_inicio - timedelta(days=hoje_inicio.weekday())
        semana_fim = semana_inicio + timedelta(days=7)
        for sala_obj in todas_as_salas:
            taxa_semana = _calcular_taxa_ocupacao(sala_obj, semana_inicio, semana_fim)
            if taxa_semana < LIMIAR_BAIXA_UTILIZACAO:
                salas_baixa_utilizacao.append({
                    "sala": sala_obj,
                    "taxa": taxa_semana,
                })

    return render(
        request,
        "webapp/dashboard.html",
        {
            "salas_disponiveis": salas_disponiveis_anotadas,
            "salas_ocupadas": salas_ocupadas_anotadas,
            "ocupadas_com_reserva": ocupadas_com_reserva_anotadas,
            "minhas_reservas": minhas_reservas,
            "agora": now,
            # RN-20
            "salas_baixa_utilizacao": salas_baixa_utilizacao,
            "limiar_baixa_utilizacao": LIMIAR_BAIXA_UTILIZACAO,
        },
    )


class SalaCreateView(UserPassesTestMixin, CreateView):
    form_class = SalaForm
    template_name = "webapp/sala_form.html"
    success_url = reverse_lazy("dashboard")

    def test_func(self):
        return self.request.user.is_staff

    def handle_no_permission(self):
        messages.error(self.request, "Apenas administradores podem gerenciar salas.")
        return redirect("dashboard")


class SalaUpdateView(UserPassesTestMixin, UpdateView):
    model = Sala
    form_class = SalaForm
    template_name = "webapp/sala_form.html"
    success_url = reverse_lazy("dashboard")

    def test_func(self):
        return self.request.user.is_staff

    def handle_no_permission(self):
        messages.error(self.request, "Apenas administradores podem gerenciar salas.")
        return redirect("dashboard")


class SalaDeleteView(UserPassesTestMixin, DeleteView):
    model = Sala
    template_name = "webapp/sala_confirm_delete.html"
    success_url = reverse_lazy("dashboard")

    def test_func(self):
        return self.request.user.is_staff

    def handle_no_permission(self):
        messages.error(self.request, "Apenas administradores podem gerenciar salas.")
        return redirect("dashboard")
        
    def delete(self, request, *args, **kwargs):
        messages.success(request, "Sala excluída com sucesso.")
        return super().delete(request, *args, **kwargs)


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
        if reserva.usuario != request.user and not request.user.is_staff:
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
        
        if reserva.usuario != request.user and not request.user.is_staff:
            messages.error(request, "Você não tem permissão para fazer check-in nesta reserva.")
            return redirect("dashboard")
            
        reserva.check_in_realizado = True
        reserva.save()
        messages.success(request, f"Check-in realizado com sucesso para a sala {reserva.sala.nome}.")
        return redirect("dashboard")


class ReservaUpdateView(UserPassesTestMixin, UpdateView):
    model = Reserva
    form_class = ReservaForm
    template_name = "webapp/reserva_form.html"
    success_url = reverse_lazy("dashboard")

    def test_func(self):
        return self.request.user.is_staff

    def handle_no_permission(self):
        messages.error(self.request, "Apenas administradores podem editar reservas.")
        return redirect("dashboard")

    def form_valid(self, form):
        messages.success(self.request, "Reserva atualizada com sucesso.")
        return super().form_valid(form)


class RelatorioOcupacaoView(UserPassesTestMixin, ListView):
    model = Reserva
    template_name = "webapp/relatorio_ocupacao.html"
    context_object_name = "reservas"

    def test_func(self):
        return self.request.user.is_staff

    def handle_no_permission(self):
        messages.error(self.request, "Acesso negado. Apenas administradores podem ver o relatório.")
        return redirect("dashboard")

    def get_queryset(self):
        qs = super().get_queryset().select_related('sala', 'usuario')
        sala_id = self.request.GET.get('sala')
        if sala_id:
            qs = qs.filter(sala_id=sala_id)
        
        data_inicio = self.request.GET.get('data_inicio')
        if data_inicio:
            qs = qs.filter(data_hora_inicio__date__gte=data_inicio)
            
        data_fim = self.request.GET.get('data_fim')
        if data_fim:
            qs = qs.filter(data_hora_inicio__date__lte=data_fim)
            
        return qs.order_by('-data_hora_inicio')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['salas'] = Sala.objects.all()
        return context


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


class SalasDisponiveisView(View):
    """RN-21: Busca de salas disponíveis em um intervalo de tempo específico."""

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect("login")
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        inicio_str = request.GET.get("inicio", "")
        fim_str = request.GET.get("fim", "")
        salas_disponiveis = None
        erro = None

        if inicio_str and fim_str:
            try:
                # Aceita formatos "YYYY-MM-DDTHH:MM" (input datetime-local)
                inicio = datetime.fromisoformat(inicio_str)
                fim = datetime.fromisoformat(fim_str)
                inicio = timezone.make_aware(inicio) if timezone.is_naive(inicio) else inicio
                fim = timezone.make_aware(fim) if timezone.is_naive(fim) else fim

                if fim <= inicio:
                    erro = "O horário de fim deve ser posterior ao de início."
                elif inicio < timezone.now():
                    erro = "O horário de início não pode estar no passado."
                else:
                    hora_inicio = inicio.time()
                    hora_fim = fim.time()

                    # Salas sem conflito de reserva no intervalo (RN-06 invertida)
                    salas_com_conflito = Reserva.objects.filter(
                        data_hora_inicio__lt=fim,
                        data_hora_fim__gt=inicio,
                    ).values_list("sala_id", flat=True)

                    # Filtra também pelo horário de disponibilidade da sala (RN-07)
                    salas_disponiveis = Sala.objects.exclude(
                        id__in=salas_com_conflito
                    ).filter(
                        hora_inicio__lte=hora_inicio,
                        hora_fim__gte=hora_fim,
                    )
            except ValueError:
                erro = "Formato de data/hora inválido."

        return render(request, "webapp/salas_disponiveis.html", {
            "salas_disponiveis": salas_disponiveis,
            "inicio": inicio_str,
            "fim": fim_str,
            "erro": erro,
        })


class ReservaRecorrenteCreateView(View):
    """RN-22 e RN-23: criação de reservas recorrentes com verificação de disponibilidade."""

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect("login")
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        form = ReservaRecorrenteForm(usuario=request.user)
        return render(request, "webapp/reserva_recorrente_form.html", {"form": form})

    def post(self, request, *args, **kwargs):
        form = ReservaRecorrenteForm(request.POST, usuario=request.user)
        if form.is_valid():
            reservas = form.criar_reservas(usuario=request.user)
            messages.success(
                request,
                f"{len(reservas)} reserva(s) recorrente(s) criada(s) com sucesso!",
            )
            return redirect("dashboard")
        return render(request, "webapp/reserva_recorrente_form.html", {"form": form})
