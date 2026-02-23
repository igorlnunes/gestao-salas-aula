from django.contrib import admin

from .models import Sala, Reserva


@admin.register(Sala)
class SalaAdmin(admin.ModelAdmin):
    list_display = ("nome", "hora_inicio", "hora_fim")


@admin.register(Reserva)
class ReservaAdmin(admin.ModelAdmin):
    list_display = ("sala", "usuario", "data_hora_inicio", "data_hora_fim")
    list_filter = ("sala",)
    date_hierarchy = "data_hora_inicio"
