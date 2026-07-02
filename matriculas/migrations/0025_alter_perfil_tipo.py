from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('matriculas', '0024_alter_pago_foto_comprobante'),
    ]

    operations = [
        migrations.AlterField(
            model_name='perfil',
            name='tipo',
            field=models.CharField(choices=[('admin', 'Administrador'), ('usuario', 'Usuario'), ('marketing', 'Marketing')], default='usuario', max_length=10),
        ),
    ]
