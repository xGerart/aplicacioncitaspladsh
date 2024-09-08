from django.test import TestCase
from django.utils import timezone
from citas.forms import CitaForm, ClienteForm
from citas.models import Servicio, Empleado

class CitaFormTest(TestCase):
    def setUp(self):
        self.servicio = Servicio.objects.create(nombre="Corte de pelo", duracion=30)
        self.empleado = Empleado.objects.create(cedula="1234567890", nombre="Ana López")

    def test_cita_form_valid(self):
        form_data = {
            'servicio': self.servicio.id,
            'empleado': self.empleado.id,
            'fecha': timezone.now().date(),
            'hora_inicio': timezone.now().time()
        }
        form = CitaForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_cita_form_invalid(self):
        form_data = {'servicio': self.servicio.id}
        form = CitaForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('empleado', form.errors)
        self.assertIn('fecha', form.errors)
        self.assertIn('hora_inicio', form.errors)

class ClienteFormTest(TestCase):
    def test_cliente_form_valid(self):
        form_data = {
            'cedula': '1234567890',
            'nombre': 'Juan Pérez',
            'email': 'juan@example.com',
            'celular': '0987654321',
            'fechanacimiento': '1990-01-01'
        }
        form = ClienteForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_cliente_form_invalid(self):
        form_data = {
            'cedula': '123',  
            'nombre': '',  
            'email': 'notanemail', 
        }
        form = ClienteForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('cedula', form.errors)
        self.assertIn('nombre', form.errors)
        self.assertIn('email', form.errors)