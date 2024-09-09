from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone
from datetime import datetime
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

class Cliente(models.Model):
    CLIENTE = 'CL'
    RECEPCIONISTA = 'RC'
    ROL_CHOICES = [
        (CLIENTE, 'Cliente'),
        (RECEPCIONISTA, 'Recepcionista'),
    ]
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)
    cedula = models.CharField(max_length=10, unique=True)
    nombre = models.CharField(max_length=100)
    apellido = models.CharField(max_length=100, null=True, blank=True)
    email = models.EmailField()
    celular = models.CharField(max_length=10)
    fechanacimiento = models.DateField()
    rol = models.CharField(max_length=2, choices=ROL_CHOICES, default=CLIENTE)

    def __str__(self):
        return f"{self.nombre} ({self.cedula})"

    def is_cliente(self):
        return self.rol == self.CLIENTE

    def is_recepcionista(self):
        return self.rol == self.RECEPCIONISTA

    def save(self, *args, **kwargs):
        if not self.rol:
            self.rol = self.CLIENTE
        super().save(*args, **kwargs)

class Servicio(models.Model):
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField()
    precio = models.DecimalField(max_digits=10, decimal_places=2)
    duracion = models.PositiveIntegerField()
    imagen = models.ImageField(upload_to='servicios/', null=True, blank=True)

    def __str__(self):
        return self.nombre

class Empleado(models.Model):
    cedula = models.CharField(max_length=10, unique=True)
    nombre = models.CharField(max_length=100)
    email = models.EmailField()
    celular = models.CharField(max_length=10)
    servicios = models.ManyToManyField(Servicio, related_name="empleados")

    @classmethod
    def get_cualquier_empleado(cls):
        return cls(id=0, nombre="Cualquier profesional")

    def __str__(self):
        return f"{self.nombre} ({self.cedula})"

    def obtener_servicios(self):
        return ", ".join([servicio.nombre for servicio in self.servicios.all()])

class Cita(models.Model):
    ESTADO_CANCELADA = 1
    ESTADO_CONFIRMADA = 2
    ESTADO_EN_PROCESO = 3
    ESTADO_TERMINADA = 4

    OPCIONES_ESTADO = [
        (ESTADO_CANCELADA, "Cita Cancelada"),
        (ESTADO_CONFIRMADA, "Cita Confirmada"),
        (ESTADO_EN_PROCESO, "En Proceso"),
        (ESTADO_TERMINADA, "Cita terminada")
    ]
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, related_name="citas")
    servicio = models.ForeignKey(Servicio, on_delete=models.CASCADE)
    empleado = models.ForeignKey(Empleado, on_delete=models.CASCADE, related_name="empleados")
    fecha = models.DateField(null=True, blank=True)
    hora_inicio = models.TimeField(null=True, blank=True)
    estado = models.IntegerField(choices=OPCIONES_ESTADO, default=ESTADO_CONFIRMADA)
    notas = models.TextField(blank=True)

    @property
    def hora_fin(self):
        if self.fecha and self.hora_inicio and self.servicio:
            return (timezone.datetime.combine(self.fecha, self.hora_inicio) + 
                    timezone.timedelta(minutes=self.servicio.duracion)).time()
        return None

    @property
    def estado_actual(self):
        if not self.fecha or not self.hora_inicio:
            return self.estado 

        ahora = timezone.now()
        fecha_hora_inicio = timezone.make_aware(timezone.datetime.combine(self.fecha, self.hora_inicio))
        
        if self.servicio:
            fecha_hora_fin = fecha_hora_inicio + timezone.timedelta(minutes=self.servicio.duracion)
        else:
            fecha_hora_fin = fecha_hora_inicio + timezone.timedelta(hours=1)  
        
        if fecha_hora_inicio <= ahora < fecha_hora_fin:
            return self.ESTADO_EN_PROCESO
        elif ahora >= fecha_hora_fin:
            return self.ESTADO_TERMINADA
        else:
            return self.estado
        
    def es_cancelable(self):
     fecha_hora_cita = timezone.make_aware(datetime.combine(self.fecha, self.hora_inicio))
     return fecha_hora_cita > timezone.now()

    def __str__(self):
        return f"Cita de {self.cliente.nombre} para {self.servicio.nombre} el {self.fecha} a las {self.hora_inicio}"

class HorarioEmpleado(models.Model):
    OPCIONES_DIAS = [
        (0, "Lunes"), (1, "Martes"), (2, "Miércoles"), (3, "Jueves"),
        (4, "Viernes"), (5, "Sábado"), (6, "Domingo"),
    ]
    empleado = models.ForeignKey(Empleado, on_delete=models.CASCADE, related_name="horarios")
    dia_semana = models.IntegerField(choices=OPCIONES_DIAS)
    hora_inicio = models.TimeField()
    hora_fin = models.TimeField()
    disponible = models.BooleanField(default=True)

    class Meta:
        unique_together = ['empleado', 'dia_semana', 'hora_inicio', 'hora_fin']

    def clean(self):
        super().clean()
        
        # Get the center's schedule for the same day
        try:
            horario_centro = HorarioCentro.objects.get(dia=self.dia_semana)
        except HorarioCentro.DoesNotExist:
            raise ValidationError(_("No hay un horario definido para el centro en este día."))

        # Check if the employee's schedule is within the center's hours
        if self.hora_inicio < horario_centro.hora_apertura or self.hora_fin > horario_centro.hora_cierre:
            raise ValidationError(_(
                "El horario del empleado debe estar dentro del horario del centro. "
                f"Horario del centro: {horario_centro.hora_apertura} - {horario_centro.hora_cierre}"
            ))

class AusenciaEmpleado(models.Model):
    empleado = models.ForeignKey(Empleado, on_delete=models.CASCADE, related_name="ausencias")
    fecha_inicio = models.DateTimeField()
    fecha_fin = models.DateTimeField()
    motivo = models.CharField(max_length=255, blank=True)

    def __str__(self):
        return f"Ausencia de {self.empleado.nombre} del {self.fecha_inicio} al {self.fecha_fin}"

class HorarioCentro(models.Model):
    DIAS_SEMANA = [
        (0, 'Lunes'), (1, 'Martes'), (2, 'Miércoles'), (3, 'Jueves'),
        (4, 'Viernes'), (5, 'Sábado'), (6, 'Domingo'),
    ]
    dia = models.IntegerField(choices=DIAS_SEMANA, unique=True)
    hora_apertura = models.TimeField()
    hora_cierre = models.TimeField()

    class Meta:
        unique_together = ['dia']

    def __str__(self):
        return f"{self.get_dia_display()}: {self.hora_apertura} - {self.hora_cierre}"