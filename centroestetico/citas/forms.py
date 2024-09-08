from django import forms
from allauth.account.forms import SignupForm
from django.db import transaction
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import datetime,date
from .models import Servicio, Empleado, Cliente, Cita

class CitaForm(forms.ModelForm):
    empleado = forms.ModelChoiceField(queryset=Empleado.objects.none(), required=False)
    fecha = forms.DateField(widget=forms.DateInput(attrs={'type': 'date', 'id': 'id_fecha'}))
    hora_inicio = forms.TimeField(widget=forms.HiddenInput(), required=False)

    class Meta:
        model = Cita
        fields = ['empleado', 'fecha', 'hora_inicio']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if 'servicio_id' in self.data:
            try:
                servicio_id = int(self.data.get('servicio_id'))
                self.fields['empleado'].queryset = Empleado.objects.filter(servicios__id=servicio_id)
            except (ValueError, TypeError):
                pass

    def clean(self):
     cleaned_data = super().clean()
     fecha = cleaned_data.get('fecha')
     hora_inicio = cleaned_data.get('hora_inicio')
     if fecha and not hora_inicio:
        raise forms.ValidationError("Por favor, selecciona una hora para la cita.")
     if fecha and hora_inicio:
        fecha_hora_cita = timezone.make_aware(datetime.combine(fecha, hora_inicio))
        if fecha_hora_cita < timezone.now():
            raise forms.ValidationError("No puedes agendar citas para fechas y horas pasadas.")
     return cleaned_data

class ClienteForm(forms.ModelForm):
    class Meta:
        model = Cliente
        fields = ['cedula', 'nombre', 'apellido', 'email', 'celular', 'fechanacimiento']
        widgets = {'fechanacimiento': forms.DateInput(attrs={'type': 'date'})}

class CombinedSignupForm(SignupForm):
    cedula = forms.CharField(max_length=10, required=True)
    nombre = forms.CharField(max_length=100, required=True)
    apellido = forms.CharField(max_length=100, required=True)
    celular = forms.CharField(max_length=10, required=True)
    fechanacimiento = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date', 'id': 'id_fechanacimiento'}),
        label="Fecha de nacimiento",
    )

    def clean_email(self):
        email = self.cleaned_data['email']
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("Este correo electrónico ya está en uso. Por favor, usa otro.")
        return email

    def clean_cedula(self):
        cedula = self.cleaned_data['cedula']
        if not self.validar_cedula(cedula):
            raise forms.ValidationError("Número de cédula inválido.")
        return cedula

    def clean_fechanacimiento(self):
        fechanacimiento = self.cleaned_data['fechanacimiento']
        hoy = datetime.now().date()
        edad = hoy.year - fechanacimiento.year - ((hoy.month, hoy.day) < (fechanacimiento.month, fechanacimiento.day))
        if edad < 18:
            raise forms.ValidationError("Debes tener al menos 18 años para registrarte.")
        return fechanacimiento

    def validar_cedula(self, cedula):
        if not cedula.isdigit() or len(cedula) != 10:
            return False
        
        provincia = int(cedula[:2])
        if provincia < 1 or provincia > 24:
            return False
        
        coeficientes = [2, 1, 2, 1, 2, 1, 2, 1, 2]
        total = 0
        
        for i in range(9):
            valor = int(cedula[i]) * coeficientes[i]
            if valor > 9:
                valor -= 9
            total += valor
        
        digito_verificador = 10 - (total % 10)
        if digito_verificador == 10:
            digito_verificador = 0
        
        return digito_verificador == int(cedula[-1])

    @transaction.atomic
    def save(self, request):
        user = super().save(request)
        user.username = self.cleaned_data['email']
        user.first_name = self.cleaned_data['nombre']
        user.last_name = self.cleaned_data['apellido']
        user.save()
        
        Cliente.objects.create(
            user=user,
            cedula=self.cleaned_data['cedula'],
            nombre=self.cleaned_data['nombre'],
            apellido=self.cleaned_data['apellido'],
            email=self.cleaned_data['email'],
            celular=self.cleaned_data['celular'],
            fechanacimiento=self.cleaned_data['fechanacimiento'],
            rol=Cliente.CLIENTE
        )
        return user