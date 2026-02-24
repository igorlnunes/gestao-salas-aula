from django.test import TestCase
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
            "hora_fim": "17:00"
        }
        form = SalaForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn("nome", form.errors)
        # Django's default uniqueness error message
        self.assertTrue(any("já existe" in str(e).lower() or "already exists" in str(e).lower() for e in form.errors["nome"]))
