from django.core.management.base import BaseCommand
from pathlib import Path
from PIL import Image
from matriculas.models import Alumno


class Command(BaseCommand):
    help = "Genera thumbnails de fotos de alumnos"

    def handle(self, *args, **kwargs):
        procesadas = 0
        for alumno in Alumno.objects.all():
            for campo in [
                'foto_previa',
                'foto_frente',
                'foto_lado',
                'foto_corte'
            ]:
                foto = getattr(alumno, campo)
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
                    procesadas += 1
                    self.stdout.write(f"OK: {thumb.name}")
                except Exception as e:
                    self.stdout.write(f"ERROR: {foto.name} {e}")
        self.stdout.write(self.style.SUCCESS(
            f"TOTAL thumbnails creados: {procesadas}"
        ))