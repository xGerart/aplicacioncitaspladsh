from django.db import models
from datetime import timedelta


class Cliente(models.Model):
    cedula = models.CharField(max_length=10, unique=True)
    nombre = models.CharField(max_length=100)
    email = models.EmailField()
    celular = models.CharField(max_length=10)
    fechanacimiento = models.DateField()

    def __str__(self):
        return f"{self.nombre} {self.cedula}"


class Servicio(models.Model):
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField()
    precio = models.DecimalField(max_digits=10, decimal_places=2)
    duracion = models.PositiveIntegerField()

    def __str__(self):
        return self.nombre


class Empleado(models.Model):
    cedula = models.CharField(max_length=10, unique=True)
    nombre = models.CharField(max_length=100)
    email = models.EmailField()
    celular = models.CharField(max_length=10)
    servicios = models.ManyToManyField("Servicio", related_name="empleados")

    def __str__(self):
        return f"{self.nombre} ({self.cedula})"

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


class HorarioEmpleado(models.Model):
    OPCIONESDIAS = [
        (0, "Lunes"),
        (1, "Martes"),
        (2, "Miércoles"),
        (3, "Jueves"),
        (4, "Viernes"),
        (5, "Sábado"),
        (6, "Domingo"),
    ]
    empleado = models.ForeignKey(
        Empleado, on_delete=models.CASCADE, related_name="horarios"
    )
    dia_semana = models.IntegerField(choices=OPCIONESDIAS)
    hora_inicio = models.TimeField()
    hora_fin = models.TimeField()
    disponible = models.BooleanField(default=True)


class AusenciaEmpleado(models.Model):
    empleado = models.ForeignKey(
        Empleado, on_delete=models.CASCADE, related_name="ausencias"
    )
    fecha_inicio = models.DateTimeField()
    fecha_fin = models.DateTimeField()
    motivo = models.CharField(max_length=255, blank=True)
