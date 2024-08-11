from django.db import models
from datetime import timedelta
from django.core.validators import MinValueValidator

# Modelo para representar a un Cliente
class Cliente(models.Model):
    cedula = models.CharField(max_length=10, unique=True)  # Número de cédula del cliente, debe ser único
    nombre = models.CharField(max_length=100)  # Nombre completo del cliente
    email = models.EmailField()  # Correo electrónico del cliente
    celular = models.CharField(max_length=10)  # Número de celular del cliente
    fechanacimiento = models.DateField()  # Fecha de nacimiento del cliente

    def __str__(self):
        return f"{self.nombre} {self.cedula}"  # Representación en cadena del cliente, útil para la administración

    class Meta:
        verbose_name = "Cliente"  # Nombre singular del modelo en el panel de administración
        verbose_name_plural = "Clientes"  # Nombre plural del modelo en el panel de administración

# Modelo para representar un Servicio
class Servicio(models.Model):
    nombre = models.CharField(max_length=100)  # Nombre del servicio
    descripcion = models.TextField()  # Descripción del servicio
    precio = models.DecimalField(max_digits=10, decimal_places=2)  # Precio del servicio con dos decimales
    duracion = models.PositiveIntegerField()  # Duración del servicio en minutos (solo valores positivos)

    def __str__(self):
        return self.nombre  # Representación en cadena del servicio, útil para la administración

    class Meta:
        verbose_name = "Servicio"  # Nombre singular del modelo en el panel de administración
        verbose_name_plural = "Servicios"  # Nombre plural del modelo en el panel de administración

# Modelo para representar a un Empleado
class Empleado(models.Model):
    cedula = models.CharField(max_length=10, unique=True)  # Número de cédula del empleado, debe ser único
    nombre = models.CharField(max_length=100)  # Nombre completo del empleado
    email = models.EmailField()  # Correo electrónico del empleado
    celular = models.CharField(max_length=10)  # Número de celular del empleado
    servicios = models.ManyToManyField('Servicio', related_name='empleados')  # Servicios que el empleado puede realizar

    def __str__(self):
        return f"{self.nombre} ({self.cedula})"  # Representación en cadena del empleado, útil para la administración

    class Meta:
        verbose_name = "Empleado"  # Nombre singular del modelo en el panel de administración
        verbose_name_plural = "Empleados"  # Nombre plural del modelo en el panel de administración

    def get_servicios(self):
        return ", ".join([servicio.nombre for servicio in self.servicios.all()])  # Devuelve una lista de nombres de los servicios asociados al empleado

# Modelo para representar una Cita
class Cita(models.Model):
    OPCIONESESTADO = [("confirmada", "Cita Confirmada"), ("cancelada", "Cita Cancelada")]  # Opciones de estado para la cita
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, related_name="citas")  # Relación con el cliente, se elimina en cascada si se elimina el cliente
    servicio = models.ForeignKey(Servicio, on_delete=models.CASCADE, related_name="servicios")  # Relación con el servicio, se elimina en cascada si se elimina el servicio
    empleado = models.ForeignKey(Empleado, on_delete=models.CASCADE, related_name="empleados")  # Relación con el empleado, se elimina en cascada si se elimina el empleado
    fechahorainicio = models.DateTimeField()  # Fecha y hora de inicio de la cita
    estado = models.CharField(max_length=10, choices=OPCIONESESTADO)  # Estado de la cita, debe ser uno de los valores en OPCIONESESTADO
    notas = models.TextField(blank=True)  # Notas adicionales sobre la cita, campo opcional

    @property
    def fechahorafin(self):
        tiempominutos = timedelta(minutes=self.servicio.duracion)  # Calcula la duración en minutos del servicio
        return self.fechahorainicio + tiempominutos  # Calcula la fecha y hora de finalización sumando la duración a la fecha de inicio

    def __str__(self):
        return f"Cita de {self.cliente.nombre} para {self.servicio.nombre}"  # Representación en cadena de la cita, útil para la administración

    class Meta:
        verbose_name = "Cita"  # Nombre singular del modelo en el panel de administración
        verbose_name_plural = "Citas"  # Nombre plural del modelo en el panel de administración
