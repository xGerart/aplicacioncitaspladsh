from django import forms
from .models import Servicio, Empleado, Cliente, Cita
from allauth.account.forms import SignupForm
from django.db import transaction

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

class ClienteForm(forms.ModelForm):
    class Meta:
        model = Cliente
        fields = ['cedula', 'nombre', 'email', 'celular', 'fechanacimiento']
        widgets = {
            'fechanacimiento': forms.DateInput(attrs={'type': 'date'}),
        }

class CombinedSignupForm(SignupForm):
    cedula = forms.CharField(max_length=10, required=True)
    nombre = forms.CharField(max_length=100, required=True)
    celular = forms.CharField(max_length=10, required=True)
    fechanacimiento = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}))

    @transaction.atomic
    def save(self, request):
        user = super(CombinedSignupForm, self).save(request)
        cliente, created = Cliente.objects.get_or_create(
            user=user,
            defaults={
                'cedula': self.cleaned_data.get('cedula'),
                'nombre': self.cleaned_data.get('nombre'),
                'email': self.cleaned_data.get('email'),
                'celular': self.cleaned_data.get('celular'),
                'fechanacimiento': self.cleaned_data.get('fechanacimiento'),
                'rol': Cliente.CLIENTE
            }
        )
        if not created: 
            for field in ['cedula', 'nombre', 'email', 'celular', 'fechanacimiento']:
                setattr(cliente, field, self.cleaned_data.get(field))
            cliente.save()
        return user