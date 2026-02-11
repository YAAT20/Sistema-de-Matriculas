from django.db import migrations, models
import uuid

def set_initial_uuids(apps, schema_editor):
    Matricula = apps.get_model('matriculas', 'Matricula')
    for row in Matricula.objects.filter(uuid__isnull=True):
        row.uuid = uuid.uuid4()
        row.save(update_fields=['uuid'])

class Migration(migrations.Migration):

    dependencies = [
        ('matriculas', '0008_alumno_fondo_social'),
    ]

    operations = [
        migrations.AddField(
            model_name='matricula',
            name='uuid',
            field=models.UUIDField(null=True, unique=True),
        ),
        migrations.RunPython(set_initial_uuids),
        migrations.AlterField(
            model_name='matricula',
            name='uuid',
            field=models.UUIDField(default=uuid.uuid4, unique=True),
        ),
    ]
