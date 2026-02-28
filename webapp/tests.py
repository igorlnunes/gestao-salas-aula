from django.test import TestCase, Client
from django.db import IntegrityError
from django.core.exceptions import ValidationError
from datetime import time

from .models import Sala, Reserva
from .forms import SalaForm
from django.utils import timezone
from datetime import timedelta

class SalaModelTest(TestCase):
    def test_sala_unique_name(self):
        """Verifica que não é possível criar duas salas com o mesmo nome."""
        Sala.objects.create(nome="Sala 101", capacidade=10, hora_inicio=time(8, 0), hora_fim=time(18, 0))
        
        with self.assertRaises(IntegrityError):
            Sala.objects.create(nome="Sala 101", capacidade=15, hora_inicio=time(9, 0), hora_fim=time(17, 0))

class ReservaModelTest(TestCase):
    def test_reserva_exceeds_sala_capacity(self):
        """Verifica que a reserva falha se a quantidade de pessoas exceder a capacidade."""
        sala = Sala.objects.create(nome="Auditório", capacidade=50, hora_inicio=time(8, 0), hora_fim=time(22, 0))
        
        inicio = timezone.now() + timedelta(days=1)
        fim = inicio + timedelta(hours=2)
        
        # Cria uma reserva válida
        reserva_valida = Reserva(
            sala=sala,
            data_hora_inicio=inicio,
            data_hora_fim=fim,
            quantidade_pessoas=50
        )
        reserva_valida.full_clean()  # Não deve lançar erro
        
        # Tenta criar uma reserva inválida (51 pessoas)
        reserva_invalida = Reserva(
            sala=sala,
            data_hora_inicio=inicio,
            data_hora_fim=fim,
            quantidade_pessoas=51
        )
        
        with self.assertRaises(ValidationError):
            reserva_invalida.full_clean()

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


class ReservaRN05Test(TestCase):
    """Testes para a regra de negócio RN-05:
    A data/hora de início da reserva deve ser anterior à de término.
    """

    def setUp(self):
        self.sala = Sala.objects.create(
            nome="Sala Teste RN05",
            capacidade=20,
            hora_inicio=time(8, 0),
            hora_fim=time(22, 0),
        )

    def test_inicio_antes_do_fim_valido(self):
        """Reserva com início < fim deve ser válida (sem ValidationError)."""
        inicio = timezone.now() + timedelta(days=1)
        fim = inicio + timedelta(hours=2)
        reserva = Reserva(sala=self.sala, data_hora_inicio=inicio, data_hora_fim=fim, quantidade_pessoas=5)
        reserva.full_clean()  # Não deve lançar exceção

    def test_inicio_igual_ao_fim_invalido(self):
        """Reserva com início == fim deve lançar ValidationError (RN-05)."""
        inicio = timezone.now() + timedelta(days=1)
        reserva = Reserva(sala=self.sala, data_hora_inicio=inicio, data_hora_fim=inicio, quantidade_pessoas=5)
        with self.assertRaises(ValidationError) as ctx:
            reserva.full_clean()
        self.assertIn("data_hora_fim", ctx.exception.message_dict)

    def test_inicio_depois_do_fim_invalido(self):
        """Reserva com início > fim deve lançar ValidationError (RN-05)."""
        fim = timezone.now() + timedelta(days=1)
        inicio = fim + timedelta(hours=1)
        reserva = Reserva(sala=self.sala, data_hora_inicio=inicio, data_hora_fim=fim, quantidade_pessoas=5)
        with self.assertRaises(ValidationError) as ctx:
            reserva.full_clean()
        self.assertIn("data_hora_fim", ctx.exception.message_dict)


class RN19TaxaOcupacaoTest(TestCase):
    """Testes para RN-19: taxa de ocupação calculada corretamente."""

    def setUp(self):
        from datetime import time
        self.sala = Sala.objects.create(
            nome="Sala RN19",
            capacidade=20,
            hora_inicio=time(8, 0),
            hora_fim=time(18, 0),
        )

    def test_taxa_zero_sem_reservas(self):
        """Sem reservas, taxa de ocupação deve ser 0."""
        from .views import _calcular_taxa_ocupacao
        hoje_inicio = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
        hoje_fim = hoje_inicio + timedelta(days=1)
        taxa = _calcular_taxa_ocupacao(self.sala, hoje_inicio, hoje_fim)
        self.assertEqual(taxa, 0)

    def test_taxa_com_reserva_parcial(self):
        """Com 5h de reserva em 10h disponíveis, taxa deve ser 50%."""
        from .views import _calcular_taxa_ocupacao
        hoje_inicio = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
        hoje_fim = hoje_inicio + timedelta(days=1)
        # Sala disponível das 8h às 18h = 10h = 600 min
        inicio_reserva = hoje_inicio.replace(hour=8, minute=0)
        fim_reserva = inicio_reserva + timedelta(hours=5)
        Reserva.objects.create(
            sala=self.sala,
            data_hora_inicio=inicio_reserva,
            data_hora_fim=fim_reserva,
        )
        taxa = _calcular_taxa_ocupacao(self.sala, hoje_inicio, hoje_fim)
        self.assertEqual(taxa, 50.0)


class RN21SalasDisponiveisTest(TestCase):
    """Testes para RN-21: busca de salas disponíveis por intervalo de tempo."""

    def setUp(self):
        from datetime import time
        from django.contrib.auth.models import User
        self.user = User.objects.create_user(username="testuser_rn21", password="pass")
        self.sala_livre = Sala.objects.create(
            nome="Sala Livre",
            capacidade=20,
            hora_inicio=time(8, 0),
            hora_fim=time(20, 0),
        )
        self.sala_ocupada = Sala.objects.create(
            nome="Sala Ocupada",
            capacidade=20,
            hora_inicio=time(8, 0),
            hora_fim=time(20, 0),
        )
        # Reserva conflitante para sala_ocupada amanhã das 10h às 12h
        amanha = timezone.now() + timedelta(days=1)
        self.inicio_conflito = amanha.replace(hour=10, minute=0, second=0, microsecond=0)
        self.fim_conflito = self.inicio_conflito + timedelta(hours=2)
        Reserva.objects.create(
            sala=self.sala_ocupada,
            data_hora_inicio=self.inicio_conflito,
            data_hora_fim=self.fim_conflito,
        )

    def test_sala_com_conflito_nao_aparece(self):
        """Sala com reserva conflitante não deve aparecer nos resultados."""
        self.client.login(username="testuser_rn21", password="pass")
        inicio_str = self.inicio_conflito.strftime("%Y-%m-%dT%H:%M")
        fim_str = self.fim_conflito.strftime("%Y-%m-%dT%H:%M")
        response = self.client.get(
            "/salas/disponiveis/",
            {"inicio": inicio_str, "fim": fim_str}
        )
        self.assertEqual(response.status_code, 200)
        salas = response.context["salas_disponiveis"]
        ids = [s.id for s in salas]
        self.assertIn(self.sala_livre.id, ids)
        self.assertNotIn(self.sala_ocupada.id, ids)

    def test_sem_parametros_nao_exibe_resultados(self):
        """Sem parâmetros, salas_disponiveis deve ser None."""
        self.client.login(username="testuser_rn21", password="pass")
        response = self.client.get("/salas/disponiveis/")
        self.assertEqual(response.status_code, 200)
        self.assertIsNone(response.context["salas_disponiveis"])


class RN22RN23ReservaRecorrenteTest(TestCase):
    """Testes para RN-22 (reservas recorrentes) e RN-23 (verificação em todas as datas)."""

    def setUp(self):
        from datetime import time
        from django.contrib.auth.models import User

        self.user = User.objects.create_user(username="testuser_rn22", password="pass")
        self.sala = Sala.objects.create(
            nome="Sala Recorrente",
            capacidade=20,
            hora_inicio=time(8, 0),
            hora_fim=time(20, 0),
        )

    def _form_data(self, **overrides):
        """Retorna dados base válidos para o formulário de recorrência."""
        amanha = (timezone.now() + timedelta(days=1)).date()
        data = {
            "sala": self.sala.pk,
            "dia_da_semana": amanha.weekday(),  # dia da semana de amanhã
            "hora_inicio": "09:00",
            "hora_fim": "11:00",
            "data_inicio_recorrencia": amanha.isoformat(),
            "num_semanas": 3,
            "quantidade_pessoas": 5,
        }
        data.update(overrides)
        return data

    def test_cria_reservas_recorrentes_com_sucesso(self):
        """Formulário válido deve criar N reservas no banco (RN-22)."""
        from .forms import ReservaRecorrenteForm

        form = ReservaRecorrenteForm(data=self._form_data(num_semanas=3), usuario=self.user)
        self.assertTrue(form.is_valid(), form.errors)
        reservas = form.criar_reservas(usuario=self.user)
        self.assertEqual(len(reservas), 3)
        self.assertEqual(Reserva.objects.count(), 3)

    def test_conflito_em_uma_data_bloqueia_tudo(self):
        """Se qualquer data tem conflito, o form deve ser inválido (RN-23)."""
        from datetime import datetime, time as dtime
        from .forms import ReservaRecorrenteForm

        amanha = (timezone.now() + timedelta(days=1)).date()
        # Cria reserva conflitante na primeira ocorrência
        dt_inicio = timezone.make_aware(datetime.combine(amanha, dtime(9, 0)))
        dt_fim = timezone.make_aware(datetime.combine(amanha, dtime(11, 0)))
        # Ajusta para o dia certo (o mesmo weekday que o form vai usar)
        Reserva.objects.create(
            sala=self.sala,
            data_hora_inicio=dt_inicio,
            data_hora_fim=dt_fim,
        )

        form = ReservaRecorrenteForm(
            data=self._form_data(dia_da_semana=amanha.weekday(), num_semanas=2),
            usuario=self.user,
        )
        self.assertFalse(form.is_valid())
        errors_text = str(form.errors)
        self.assertIn("Conflito", errors_text)

    def test_limite_semanas_excedido(self):
        """num_semanas > 12 deve tornar o formulário inválido (RN-22)."""
        from .forms import ReservaRecorrenteForm

        form = ReservaRecorrenteForm(data=self._form_data(num_semanas=13), usuario=self.user)
        self.assertFalse(form.is_valid())
        self.assertIn("num_semanas", form.errors)

    def test_hora_fim_antes_hora_inicio_invalido(self):
        """hora_fim <= hora_inicio deve tornar o formulário inválido."""
        from .forms import ReservaRecorrenteForm

        form = ReservaRecorrenteForm(
            data=self._form_data(hora_inicio="11:00", hora_fim="09:00"),
            usuario=self.user,
        )
        self.assertFalse(form.is_valid())

    def test_data_no_passado_invalida(self):
        """data_inicio_recorrencia no passado deve tornar o formulário inválido (RN-08)."""
        from .forms import ReservaRecorrenteForm
        from datetime import date, timedelta as td

        ontem = (timezone.now() - td(days=1)).date()
        form = ReservaRecorrenteForm(
            data=self._form_data(data_inicio_recorrencia=ontem.isoformat()),
            usuario=self.user,
        )
        self.assertFalse(form.is_valid())
