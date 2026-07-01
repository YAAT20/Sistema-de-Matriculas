from django.db import transaction
from django.db.models import Prefetch

from marketing.models import (
    Publicacion,
    ArchivoPublicacion,
)

class PublicacionService:

    @staticmethod
    def listar():
        return PublicacionService._base_queryset()

    @staticmethod
    def obtener(pk):
        return PublicacionService._base_queryset().get(pk=pk)

    @staticmethod
    def pendientes():
        return PublicacionService._base_queryset().filter(
            estado="pendiente"
        )

    @staticmethod
    def borradores():
        return PublicacionService._base_queryset().filter(
            estado="borrador"
        )

    @staticmethod
    def aprobadas():
        return PublicacionService._base_queryset().filter(
            estado="aprobada"
        )

    @staticmethod
    def publicadas():
        return PublicacionService._base_queryset().filter(
            estado="publicada"
        )

    @staticmethod
    @transaction.atomic
    def crear(form, copy_formset, archivo_formset):
        publicacion = form.save()
        copy_formset.instance = publicacion
        archivo_formset.instance = publicacion
        copy_formset.save()
        archivo_formset.save()
        return publicacion

    @staticmethod
    @transaction.atomic
    def actualizar(publicacion, form, copy_formset, archivo_formset):
        publicacion = form.save()
        copy_formset.instance = publicacion
        archivo_formset.instance = publicacion
        copy_formset.save()
        archivo_formset.save()
        return publicacion

    @staticmethod
    def eliminar(publicacion):
        publicacion.delete()

    @staticmethod
    def cambiar_estado(publicacion, estado):
        publicacion.estado = estado
        publicacion.save(update_fields=["estado"])
        return publicacion

    @staticmethod
    def _base_queryset():
        return (
            Publicacion.objects
            .select_related("evento")
            .prefetch_related(
                "copies",
                Prefetch(
                    "archivos",
                    queryset=ArchivoPublicacion.objects.order_by("orden")
                )
            )
        )