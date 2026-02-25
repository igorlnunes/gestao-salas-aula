from django.urls import path

from . import views

urlpatterns = [
    path("", views.welcome, name="welcome"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path("salas/nova/", views.SalaCreateView.as_view(), name="sala_create"),
    path("reservas/nova/", views.ReservaCreateView.as_view(), name="reserva_create"),
    path("login/", views.LoginViewCustom.as_view(), name="login"),
    path("logout/", views.LogoutViewCustom.as_view(), name="logout"),
    path("cadastro/", views.RegistroView.as_view(), name="register"),
]
