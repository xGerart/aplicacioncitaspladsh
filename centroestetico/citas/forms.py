from django import forms
from .models import Servicio, Empleado, Cliente, Cita

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