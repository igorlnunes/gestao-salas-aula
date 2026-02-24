from django.test import TestCase, Client
from django.db import IntegrityError
from datetime import time

from .models import Sala
from .forms import SalaForm

class SalaModelTest(TestCase):
    def test_sala_unique_name(self):
        """Verifica que não é possível criar duas salas com o mesmo nome."""
        Sala.objects.create(nome="Sala 101", hora_inicio=time(8, 0), hora_fim=time(18, 0))
        
        with self.assertRaises(IntegrityError):
            Sala.objects.create(nome="Sala 101", hora_inicio=time(9, 0), hora_fim=time(17, 0))

class SalaFormTest(TestCase):
    def test_sala_form_unique_name(self):
        """Verifica que o formulário valida a unicidade do nome."""
        Sala.objects.create(nome="Sala 101", hora_inicio=time(8, 0), hora_fim=time(18, 0))
        
        data = {
            "nome": "Sala 101",
            "hora_inicio": "09:00",
            "hora_fim": "17:00",
            "capacidade": 30 # Added missing field
        }
        form = SalaForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn("nome", form.errors)
        # Django's default uniqueness error message
        self.assertTrue(any("já existe" in str(e).lower() or "already exists" in str(e).lower() for e in form.errors["nome"]))

class ViewTest(TestCase):
    def test_base_template(self):
        """Verifica se o template base contém os elementos do modo noturno."""
        client = Client()
        # Assuming welcome page is at root '/' or 'welcome'
        response = client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'webapp/css/style.css')
        self.assertContains(response, 'webapp/js/theme.js')
        self.assertContains(response, 'id="theme-toggle"')
