from django.test import TestCase
from django.utils import timezone
from datetime import timedelta
from citas.models import Cliente, Empleado, Servicio, Cita

class ClienteModelTest(TestCase):
    def setUp(self):
        self.cliente = Cliente.objects.create(
            cedula="1234567890",
            nombre="Juan Pérez",
            fechanacimiento="1990-01-01",
            email="juan@example.com",
            rol=Cliente.CLIENTE
        )

    def test_is_cliente(self):
        self.assertTrue(self.cliente.is_cliente())

    def test_is_recepcionista(self):
        recepcionista = Cliente.objects.create(
            cedula="0987654321",
            nombre="Ana López",
            email="ana@example.com",
            rol=Cliente.RECEPCIONISTA
        )
        self.assertTrue(recepcionista.is_recepcionista())

class CitaModelTest(TestCase):
    def setUp(self):
        self.cliente = Cliente.objects.create(cedula="1234567890", nombre="Juan Pérez")
        self.empleado = Empleado.objects.create(cedula="0987654321", nombre="Ana López")
        self.servicio = Servicio.objects.create(nombre="Corte de pelo", duracion=30)
        
    def test_es_cancelable(self):
        # Cita futura
        cita_futura = Cita.objects.create(
            cliente=self.cliente,
            empleado=self.empleado,
            servicio=self.servicio,
            fecha=timezone.now().date() + timedelta(days=1),
            hora_inicio=timezone.now().time()
        )
        self.assertTrue(cita_futura.es_cancelable())

        # Cita pasada
        cita_pasada = Cita.objects.create(
            cliente=self.cliente,
            empleado=self.empleado,
            servicio=self.servicio,
            fecha=timezone.now().date() - timedelta(days=1),
            hora_inicio=timezone.now().time()
        )
        self.assertFalse(cita_pasada.es_cancelable())

    def test_estado_actual(self):
        now = timezone.now()
        cita = Cita.objects.create(
            cliente=self.cliente,
            empleado=self.empleado,
            servicio=self.servicio,
            fecha=now.date(),
            hora_inicio=(now - timedelta(minutes=15)).time(),
            estado=Cita.ESTADO_CONFIRMADA
        )
        self.assertEqual(cita.estado_actual, Cita.ESTADO_EN_PROCESO)