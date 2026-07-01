from django.contrib import admin
from .models import (
    Evento,
    FotoEvento,
    Publicacion,
    CopyPublicacion,
    ArchivoPublicacion,
    RecursoMarketing
)

class FotoEventoInline(admin.TabularInline):
    model = FotoEvento
    extra = 1

class CopyPublicacionInline(admin.TabularInline):
    model = CopyPublicacion
    extra = 4
    max_num = 4

class ArchivoPublicacionInline(admin.TabularInline):
    model = ArchivoPublicacion
    extra = 1

@admin.register(Evento)
class EventoAdmin(admin.ModelAdmin):

    list_display = (
        'nombre',
        'fecha_inicio',
        'lugar',
        'estado',
    )

    list_filter = (
        'estado',
        'fecha_inicio',
    )

    search_fields = (
        'nombre',
        'lugar',
    )

    date_hierarchy = 'fecha_inicio'

    inlines = [
        FotoEventoInline
    ]


@admin.register(Publicacion)
class PublicacionAdmin(admin.ModelAdmin):

    list_display = (
        'titulo',
        'estado',
        'evento',
        'fecha_programada',
        'creado_en',
    )

    list_filter = (
        'estado',
        'creado_en',
    )

    search_fields = (
        'titulo',
    )

    readonly_fields = (
        'creado_en',
        'actualizado_en',
    )

    inlines = [
        CopyPublicacionInline,
        ArchivoPublicacionInline
    ]

@admin.register(RecursoMarketing)
class RecursoMarketingAdmin(admin.ModelAdmin):

    list_display = (
        'nombre',
        'categoria',
        'creado_en',
    )

    list_filter = (
        'categoria',
    )

    search_fields = (
        'nombre',
        'descripcion',
    )
