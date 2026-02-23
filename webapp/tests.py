from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from .models import Sala, Reserva
from django.utils import timezone
import datetime

class SalaModelTest(TestCase):
    def test_create_sala(self):
        sala = Sala.objects.create(
            nome="Sala 1",
            hora_inicio=datetime.time(9, 0),
            hora_fim=datetime.time(17, 0)
        )
        self.assertEqual(sala.nome, "Sala 1")
        self.assertEqual(str(sala), "Sala 1")

class ReservaModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="testuser", password="password")
        self.sala = Sala.objects.create(
            nome="Sala 1",
            hora_inicio=datetime.time(9, 0),
            hora_fim=datetime.time(17, 0)
        )

    def test_create_reserva(self):
        start = timezone.now()
        end = start + datetime.timedelta(hours=1)
        reserva = Reserva.objects.create(
            sala=self.sala,
            usuario=self.user,
            data_hora_inicio=start,
            data_hora_fim=end
        )
        self.assertEqual(reserva.sala, self.sala)
        self.assertEqual(reserva.usuario, self.user)

class ViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username="testuser", password="password")
        self.sala = Sala.objects.create(
            nome="Sala 1",
            hora_inicio=datetime.time(9, 0),
            hora_fim=datetime.time(17, 0)
        )

    def test_dashboard_access_denied_anonymous(self):
        response = self.client.get(reverse('dashboard'))
        self.assertNotEqual(response.status_code, 200)
        # Should redirect to login
        self.assertEqual(response.status_code, 302)

    def test_dashboard_access_allowed_authenticated(self):
        self.client.login(username="testuser", password="password")
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Sala 1")

    def test_login_view(self):
        response = self.client.get(reverse('login'))
        self.assertEqual(response.status_code, 200)

    def test_register_view(self):
        response = self.client.get(reverse('register'))
        self.assertEqual(response.status_code, 200)

        # Test registration
        response = self.client.post(reverse('register'), {
            'username': 'newuser',
            'password': 'newpassword123',
            'password_confirm': 'newpassword123'
        })
        # Should redirect to welcome
        self.assertEqual(response.status_code, 302)
        self.assertTrue(User.objects.filter(username='newuser').exists())

    def test_sala_create_view(self):
        self.client.login(username="testuser", password="password")
        response = self.client.post(reverse('sala_create'), {
            'nome': 'Sala 2',
            'hora_inicio': '10:00',
            'hora_fim': '12:00'
        })
        self.assertEqual(response.status_code, 302) # Redirect to dashboard
        self.assertTrue(Sala.objects.filter(nome='Sala 2').exists())
