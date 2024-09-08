from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from ..models import Cliente

class SecurityTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user_cliente = User.objects.create_user(username='cliente', password='12345')
        self.user_recepcionista = User.objects.create_user(username='recepcionista', password='12345')
        Cliente.objects.create(user=self.user_cliente, cedula="1234567890", nombre="Cliente Test", rol=Cliente.CLIENTE)
        Cliente.objects.create(user=self.user_recepcionista, cedula="0987654321", nombre="Recepcionista Test", rol=Cliente.RECEPCIONISTA)

    def test_cliente_cannot_access_recepcionista_view(self):
        self.client.login(username='cliente', password='12345')
        response = self.client.get(reverse('gestion_citas'))
        self.assertEqual(response.status_code, 403)  

    def test_recepcionista_cannot_access_cliente_view(self):
        self.client.login(username='recepcionista', password='12345')
        response = self.client.get(reverse('agendar_cita'))
        self.assertEqual(response.status_code, 403) 

    def test_unauthenticated_user_redirect(self):
        response = self.client.get(reverse('agendar_cita'))
        self.assertEqual(response.status_code, 302)  
        self.assertTrue(response.url.startswith('/accounts/login/'))