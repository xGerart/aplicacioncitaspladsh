from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('citas', '0001_initial'),  # Asegúrate de que este sea el nombre correcto de la migración anterior
    ]

    operations = [
        migrations.AddField(
            model_name='cliente',
            name='rol',
            field=models.CharField(choices=[('CL', 'Cliente'), ('RC', 'Recepcionista')], default='CL', max_length=2),
        ),
    ]