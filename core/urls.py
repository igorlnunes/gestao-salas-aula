from django.urls import path
from . import views

urlpatterns = [
    path('', views.welcome, name='welcome'),
    path('rooms/', views.RoomListView.as_view(), name='room_list'),
    path('rooms/add/', views.RoomCreateView.as_view(), name='room_add'),
]
