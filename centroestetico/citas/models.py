from django.db import models
from datetime import timedelta
from django.core.validators import MinValueValidator


class Cliente(models.Model):
    cedula = models.CharField(max_length=10, unique=True)
    nombre = models.CharField(max_length=100)
    email = models.EmailField()
    celular = models.CharField(max_length=10)
    fechanacimiento = models.DateField()

    def __str__(self):
        return f"{self.nombre} {self.cedula}"

    class Meta:
        verbose_name = "Cliente"
        verbose_name_plural = "Clientes"


class Servicio(models.Model):
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField()
    precio = models.DecimalField(max_digits=10, decimal_places=2)
    duracion = models.PositiveIntegerField()

    def __str__(self):
        return self.nombre

    class Meta:
        verbose_name = "Servicio"
        verbose_name_plural = "Servicios"


class Empleado(models.Model):
    cedula = models.CharField(max_length=10, unique=True)
    nombre = models.CharField(max_length=100)
    email = models.EmailField()
    celular = models.CharField(max_length=10)
    servicios = models.ManyToManyField("Servicio", related_name="empleados")

    def __str__(self):
        return f"{self.nombre} ({self.cedula})"

    class Meta:
        verbose_name = "Empleado"
        verbose_name_plural = "Empleados"

    def get_servicios(self):
        return ", ".join([servicio.nombre for servicio in self.servicios.all()])


class Cita(models.Model):
    OPCIONESESTADO = [
        ("confirmada", "Cita Confirmada"),
        ("cancelada", "Cita Cancelada"),
    ]
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, related_name="citas")
    servicio = models.ForeignKey(
        Servicio, on_delete=models.CASCADE, related_name="servicios"
    )
    empleado = models.ForeignKey(
        Empleado, on_delete=models.CASCADE, related_name="empleados"
    )
    fechahorainicio = models.DateTimeField()
    estado = models.CharField(max_length=10, choices=OPCIONESESTADO)
    notas = models.TextField(blank=True)

    @property
    def fechahorafin(self):
        tiempominutos = timedelta(minutes=self.servicio.duracion)
        return self.fechahorainicio + tiempominutos

    def __str__(self):
        return f"Cita de {self.cliente.nombre} para {self.servicio.nombre}"

    class Meta:
        verbose_name = "Cita"
        verbose_name_plural = "Citas"

class HorarioEmpleado(models.Model):
    empleado = models.ForeignKey(Empleado, on_delete=models.CASCADE, related_name='horarios')
    dia_semana = models.IntegerField(choices=[(i, day) for i, day in enumerate(['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo'])])
    hora_inicio = models.TimeField()
    hora_fin = models.TimeField()
    disponible = models.BooleanField(default=True)

    class Meta:
        unique_together = ('empleado', 'dia_semana')

class AusenciaEmpleado(models.Model):
    empleado = models.ForeignKey(Empleado, on_delete=models.CASCADE, related_name='ausencias')
    fecha_inicio = models.DateTimeField()
    fecha_fin = models.DateTimeField()
    motivo = models.CharField(max_length=255, blank=True)