from django import forms
from allauth.account.forms import SignupForm
from django.db import transaction
from .models import Servicio, Empleado, Cliente, Cita

# Formulario relacionado con Citas
class CitaForm(forms.ModelForm):
    servicio = forms.ModelChoiceField(
        queryset=Servicio.objects.all(),
        widget=forms.Select(attrs={'id': 'id_servicio'}),
        empty_label=None
    )
    empleado = forms.ModelChoiceField(
        queryset=Empleado.objects.none(),
        required=False
    )
    fecha = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date', 'id': 'id_fecha'})
    )
    hora_inicio = forms.TimeField(
        widget=forms.HiddenInput()
    )

    class Meta:
        model = Cita
        fields = ['servicio', 'empleado', 'fecha', 'hora_inicio']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if 'servicio' in self.data:
            try:
                servicio_id = int(self.data.get('servicio'))
                self.fields['empleado'].queryset = Empleado.objects.filter(servicios__id=servicio_id)
            except (ValueError, TypeError):
                pass

# Formulario relacionado con Clientes
class ClienteForm(forms.ModelForm):
    class Meta:
        model = Cliente
        fields = ['cedula', 'nombre','apellido', 'email', 'celular', 'fechanacimiento']
        widgets = {
            'fechanacimiento': forms.DateInput(attrs={'type': 'date'}),
        }

# Formulario combinado para registro de usuario y cliente
class CombinedSignupForm(SignupForm):
    cedula = forms.CharField(max_length=10, required=True)
    nombre = forms.CharField(max_length=100, required=True)
    apellido = forms.CharField(max_length=100, required=True)
    celular = forms.CharField(max_length=10, required=True)
    fechanacimiento = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}))

    @transaction.atomic
    def save(self, request):
        user = super(CombinedSignupForm, self).save(request)
        user.first_name = self.cleaned_data['nombre']
        user.last_name = self.cleaned_data['apellido']
        user.username = ''  # Dejar el username en blanco
        user.save()
        
        cliente = Cliente.objects.create(
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