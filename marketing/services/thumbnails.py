import os
import subprocess
from io import BytesIO
from pathlib import Path
from PIL import Image
from django.core.files.base import ContentFile

class ThumbnailService:
    SIZE = (400, 400)
    @classmethod
    def generar(cls, archivo_publicacion):
        if archivo_publicacion.tipo == "imagen":
            cls._imagen(archivo_publicacion)
        elif archivo_publicacion.tipo == "video":
            cls._video(archivo_publicacion)

    @classmethod
    def _imagen(cls, archivo_publicacion):
        with Image.open(archivo_publicacion.archivo) as imagen:
            imagen.thumbnail(cls.SIZE)
            if imagen.mode != "RGB":
                imagen = imagen.convert("RGB")
            salida = BytesIO()

            imagen.save(
                salida,
                format="JPEG",
                quality=85,
                optimize=True
            )

            nombre = Path(
                archivo_publicacion.archivo.name
            ).stem

            archivo_publicacion.thumbnail.save(
                f"{nombre}_thumb.jpg",
                ContentFile(salida.getvalue()),
                save=False
            )

            salida.close()

    @classmethod
    def _video(cls, archivo_publicacion):

        nombre = Path(
            archivo_publicacion.archivo.name
        ).stem

        origen = archivo_publicacion.archivo.path

        salida = Path(origen).parent / f"{nombre}_thumb.jpg"

        comando = [
            "ffmpeg",
            "-y",
            "-i",
            origen,
            "-ss",
            "00:00:01",
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

            if salida.exists():

                with open(salida, "rb") as imagen:

                    archivo_publicacion.thumbnail.save(
                        f"{nombre}_thumb.jpg",
                        ContentFile(imagen.read()),
                        save=False,
                    )

                os.remove(salida)

        except Exception:
            pass