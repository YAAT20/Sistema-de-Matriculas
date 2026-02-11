from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import Perfil
from django.db.models.signals import post_save
from matriculas.models import Alumno
from django.db.models.signals import post_save, post_delete
from matriculas.models import Matricula

@receiver(post_save, sender=User)
def crear_perfil_usuario(sender, instance, created, **kwargs):
    if created:
        Perfil.objects.create(user=instance)

@receiver(post_save, sender=User)
def guardar_perfil_usuario(sender, instance, **kwargs):
    if hasattr(instance, 'perfil'):
        instance.perfil.save()

def mapear_grado(grado_estudios):
    mapping = {
        '1s': 1,
        '2s': 2,
        '3s': 3,
        '4s': 4,
        '5s': 5,
        'pre': 6
    }
    return mapping.get(grado_estudios, 1)    

@receiver([post_save, post_delete], sender=Matricula)
def actualizar_estado_alumno(sender, instance, **kwargs):
    alumno = instance.alumno
    tiene_matriculas = alumno.matriculas.exists()
    if alumno.activo != tiene_matriculas:
        alumno.activo = tiene_matriculas
        alumno.save(update_fields=['activo'])
