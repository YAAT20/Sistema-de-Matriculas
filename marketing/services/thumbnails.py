import os
import subprocess
from io import BytesIO
from pathlib import Path

from PIL import Image
from django.core.files.base import ContentFile


class ThumbnailService:
    SIZE = (400, 400)

    EXTENSIONES_VIDEO = (
        ".mp4",
        ".avi",
        ".mov",
        ".mkv",
        ".webm",
        ".m4v",
    )

    EXTENSIONES_IMAGEN = (
        ".jpg",
        ".jpeg",
        ".png",
        ".gif",
        ".bmp",
        ".webp",
    )

    @classmethod
    def generar(cls, instancia_media):

        # FotoEvento usa "imagen"
        if hasattr(instancia_media, "imagen"):
            archivo = instancia_media.imagen

        # ArchivoPublicacion usa "archivo"
        elif hasattr(instancia_media, "archivo"):
            archivo = instancia_media.archivo

        else:
            raise ValueError(
                f"{instancia_media.__class__.__name__} "
                "no tiene campo imagen ni archivo"
            )

        if not archivo:
            return False

        nombre = archivo.name.lower()

        if nombre.endswith(cls.EXTENSIONES_VIDEO):
            return cls._video(instancia_media, archivo)

        if nombre.endswith(cls.EXTENSIONES_IMAGEN):
            return cls._imagen(instancia_media, archivo)

        return False

    @classmethod
    def _imagen(cls, instancia_media, archivo):

        with Image.open(archivo) as imagen:

            imagen.thumbnail(cls.SIZE)

            if imagen.mode != "RGB":
                imagen = imagen.convert("RGB")

            salida = BytesIO()

            imagen.save(
                salida,
                format="JPEG",
                quality=85,
                optimize=True,
            )

            nombre = Path(archivo.name).stem

            instancia_media.thumbnail.save(
                f"{nombre}_thumb.jpg",
                ContentFile(salida.getvalue()),
                save=False,
            )

        return True

    @classmethod
    def _video(cls, instancia_media, archivo):

        nombre = Path(archivo.name).stem
        origen = archivo.path

        salida = Path(origen).parent / f"{nombre}_thumb.jpg"

        comando = [
            "ffmpeg",
            "-y",
            "-ss",
            "00:00:01",
            "-i",
            origen,
            "-vframes",
            "1",
            str(salida),
        ]

        try:

            subprocess.run(
                comando,
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )

            if not salida.exists():
                return False

            with open(salida, "rb") as img_file:
                instancia_media.thumbnail.save(
                    f"{nombre}_thumb.jpg",
                    ContentFile(img_file.read()),
                    save=False,
                )

            os.remove(salida)

            return True

        except Exception as e:

            print(
                f"Error generando thumbnail de video: {e}"
            )

            if salida.exists():
                os.remove(salida)

            return False