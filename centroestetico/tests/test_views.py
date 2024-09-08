from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from ..models import Cliente, Servicio, Empleado, Cita

class ViewsTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='12345')
        self.cliente = Cliente.objects.create(user=self.user, cedula="1234567890", nombre="Test User", rol=Cliente.CLIENTE)
        self.servicio = Servicio.objects.create(nombre="Corte de pelo", duracion=30)
        self.empleado = Empleado.objects.create(cedula="0987654321", nombre="Ana López")

    def test_home_view(self):
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'home.html')

    def test_agendar_cita_view(self):
        self.client.login(username='testuser', password='12345')
        response = self.client.get(reverse('agendar_cita'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'cita.html')

    def test_ver_citas_view(self):
        self.client.login(username='testuser', password='12345')
        response = self.client.get(reverse('ver_citas'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'ver_citas.html')

class AjaxViewsTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.servicio = Servicio.objects.create(nombre="Corte de pelo", duracion=30)
        self.empleado = Empleado.objects.create(cedula="0987654321", nombre="Ana López")
        self.empleado.servicios.add(self.servicio)

    def test_get_empleados_disponibles(self):
        response = self.client.get(reverse('get_empleados_disponibles'), {'servicio': self.servicio.id})
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(str(response.content, encoding='utf8'), {
            "empleados": [{"id": self.empleado.id, "nombre": "Ana López"}]
        })

    def test_get_bloques_disponibles(self):
        response = self.client.get(reverse('get_bloques_disponibles'), {
            'empleado': self.empleado.id,
            'servicio': self.servicio.id,
            'fecha': '2023-01-01'
        })
        self.assertEqual(response.status_code, 200)
        # Verifica que la respuesta contiene 'bloques' o 'mensaje'
        content = response.json()
        self.assertTrue('bloques' in content or 'mensaje' in content)