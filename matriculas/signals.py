from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import Perfil
from django.db.models.signals import post_save
from matriculas.models import Matricula, Apoderado
from django.db.models.signals import post_save, post_delete
from django.db.models.signals import m2m_changed
from django.dispatch import receiver
from pathlib import Path
from PIL import Image
from .models import Alumno

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

@receiver(m2m_changed, sender=Apoderado.alumnos.through)
def actualizar_estado_apoderado_m2m(sender, instance, **kwargs):
    instance.actualizar_estado()

@receiver(post_save, sender=Alumno)
def generar_thumbnails_alumno(sender, instance, created, **kwargs):
    campos = [
        'foto_previa',
        'foto_frente',  
        'foto_lado',
        'foto_corte'
    ]
    for campo in campos:
        foto = getattr(instance, campo)
        if not foto:
            continue
        try:
            ruta = Path(foto.path)
            if not ruta.exists():
                continue
            thumb = ruta.with_name(ruta.stem + "_thumb.jpg")
            if thumb.exists():
                continue
            img = Image.open(ruta)
            img.thumbnail((300, 300))
            if img.mode != "RGB":
                img = img.convert("RGB")
            img.save(
                thumb,
                format="JPEG",
                quality=60,
                optimize=True
            )
        except Exception:
            continue