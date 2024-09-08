from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from ..models import Cliente, Servicio, Empleado, Cita

class AgendarCitaIntegrationTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='12345')
        self.cliente = Cliente.objects.create(user=self.user, cedula="1234567890", nombre="Test User", rol=Cliente.CLIENTE)
        self.servicio = Servicio.objects.create(nombre="Corte de pelo", duracion=30)
        self.empleado = Empleado.objects.create(cedula="0987654321", nombre="Ana López")
        self.empleado.servicios.add(self.servicio)

    def test_agendar_cita_flow(self):
        self.client.login(username='testuser', password='12345')

        # Paso 1: Obtener empleados disponibles
        response = self.client.get(reverse('get_empleados_disponibles'), {'servicio': self.servicio.id})
        self.assertEqual(response.status_code, 200)
        content = response.json()
        self.assertTrue(len(content['empleados']) > 0)

        # Paso 2: Obtener bloques disponibles
        response = self.client.get(reverse('get_bloques_disponibles'), {
            'empleado': self.empleado.id,
            'servicio': self.servicio.id,
            'fecha': '2023-01-01'
        })
        self.assertEqual(response.status_code, 200)
        content = response.json()
        self.assertTrue('bloques' in content or 'mensaje' in content)

        # Paso 3: Agendar cita
        response = self.client.post(reverse('agendar_cita'), {
            'servicio': self.servicio.id,
            'empleado': self.empleado.id,
            'fecha': '2023-01-01',
            'hora_inicio': '10:00'
        })
        self.assertEqual(response.status_code, 302)  # Redirección después de éxito

        # Verificar que la cita se creó
        self.assertTrue(Cita.objects.filter(cliente=self.cliente, servicio=self.servicio).exists())