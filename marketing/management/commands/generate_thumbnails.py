from django.core.management.base import BaseCommand
from marketing.models import FotoEvento, ArchivoPublicacion
from marketing.services.thumbnails import ThumbnailService


class Command(BaseCommand):
    help = "Genera thumbnails para archivos existentes"

    def handle(self, *args, **kwargs):
        total = 0
        errores = 0

        # FOTO EVENTO
        self.stdout.write("Procesando FotoEvento...")
        fotos = FotoEvento.objects.filter(thumbnail__isnull=True)

        for foto in fotos:
            if not foto.imagen:
                continue

            try:
                resultado = ThumbnailService.generar(foto)
                if resultado:
                    foto.save(update_fields=["thumbnail"])
                    total += 1
                    self.stdout.write(
                        self.style.SUCCESS(f"OK FotoEvento #{foto.pk}")
                    )
            except Exception as e:
                errores += 1
                self.stdout.write(
                    self.style.ERROR(f"ERROR FotoEvento #{foto.pk}: {e}")
                )

        # ARCHIVO PUBLICACION
        self.stdout.write("Procesando ArchivoPublicacion...")
        archivos = ArchivoPublicacion.objects.filter(thumbnail__isnull=True)

        for archivo in archivos:
            if not archivo.archivo:
                continue
            if archivo.tipo not in ("imagen", "video"):
                continue

            try:
                resultado = ThumbnailService.generar(archivo)
                if resultado:
                    archivo.save(update_fields=["thumbnail"])
                    total += 1
                    self.stdout.write(
                        self.style.SUCCESS(
                            f"OK ArchivoPublicacion #{archivo.pk}"
                        )
                    )
            except Exception as e:
                errores += 1
                self.stdout.write(
                    self.style.ERROR(
                        f"ERROR ArchivoPublicacion #{archivo.pk}: {e}"
                    )
                )

        # RESULTADO
        self.stdout.write("")
        self.stdout.write(
            self.style.SUCCESS(f"TOTAL thumbnails creados: {total}")
        )

        if errores:
            self.stdout.write(
                self.style.ERROR(f"TOTAL errores: {errores}")
            )