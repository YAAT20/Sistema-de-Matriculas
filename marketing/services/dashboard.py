from datetime import timedelta
from django.db.models import Count, Q
from django.utils import timezone
from marketing.models import (
    Evento,
    Publicacion,
    FotoEvento,
    RecursoMarketing
)
from matriculas.models import Alumno


class DashboardMarketingService:

    @staticmethod
    def obtener_metricas():

        ahora = timezone.now()

        eventos_futuros = Evento.objects.filter(
            fecha_inicio__gte=ahora
        )

        evento_con_mas_fotos = (
            Evento.objects
            .annotate(total_fotos=Count('fotos'))
            .order_by('-total_fotos')
            .first()
        )

        publicacion_mas_antigua = (
            Publicacion.objects
            .exclude(estado='publicada')
            .order_by('creado_en')
            .first()
        )

        alumnos_completos = (
            Alumno.objects
            .exclude(
                Q(foto_previa__isnull=True) |
                Q(foto_previa='')
            )
            .exclude(
                Q(foto_frente__isnull=True) |
                Q(foto_frente='')
            )
            .exclude(
                Q(foto_lado__isnull=True) |
                Q(foto_lado='')
            )
            .exclude(
                Q(foto_corte__isnull=True) |
                Q(foto_corte='')
            )
        )

        alumnos_incompletos = (
            Alumno.objects.filter(
                Q(foto_previa__isnull=True) |
                Q(foto_previa='') |
                Q(foto_frente__isnull=True) |
                Q(foto_frente='') |
                Q(foto_lado__isnull=True) |
                Q(foto_lado='') |
                Q(foto_corte__isnull=True) |
                Q(foto_corte='')
            )
        )

        eventos_sin_fotos = (
            Evento.objects
            .annotate(total_fotos=Count('fotos'))
            .filter(total_fotos=0)
        )

        publicaciones_pendientes = (
            Publicacion.objects
            .exclude(estado='publicada')
            .order_by('creado_en')
        )

        return {

            'eventos_futuros':
                eventos_futuros.count(),

            'eventos_mes':
                eventos_futuros.filter(
                    fecha_inicio__lte=ahora + timedelta(days=30)
                ).count(),

            'eventos_realizados':
                Evento.objects.filter(
                    estado='realizado'
                ).count(),

            'eventos_cancelados':
                Evento.objects.filter(
                    estado='cancelado'
                ).count(),

            'proximos_eventos':
                eventos_futuros.order_by(
                    'fecha_inicio'
                )[:5],

            'eventos_sin_fotos':
                eventos_sin_fotos,

            'cantidad_eventos_sin_fotos':
                eventos_sin_fotos.count(),

            'evento_con_mas_fotos':
                evento_con_mas_fotos,

            'total_publicaciones':
                Publicacion.objects.count(),

            'publicaciones_borrador':
                Publicacion.objects.filter(
                    estado='borrador'
                ).count(),

            'publicaciones_pendientes':
                Publicacion.objects.filter(
                    estado='pendiente'
                ).count(),

            'publicaciones_publicadas':
                Publicacion.objects.filter(
                    estado='publicada'
                ).count(),

            'publicaciones_pendientes_lista':
                publicaciones_pendientes[:10],

            'publicacion_mas_antigua':
                publicacion_mas_antigua,

            'total_fotos_eventos':
                FotoEvento.objects.count(),

            'total_recursos':
                RecursoMarketing.objects.count(),

            'total_imagenes':
                RecursoMarketing.objects.filter(
                    categoria='imagen'
                ).count(),

            'total_videos':
                RecursoMarketing.objects.filter(
                    categoria='video'
                ).count(),

            'total_plantillas':
                RecursoMarketing.objects.filter(
                    categoria='plantilla'
                ).count(),

            'total_alumnos':
                Alumno.objects.count(),

            'alumnos_completos':
                alumnos_completos.count(),

            'alumnos_incompletos':
                alumnos_incompletos.count(),

            'sin_foto_previa':
                Alumno.objects.filter(
                    Q(foto_previa__isnull=True) |
                    Q(foto_previa='')
                ).count(),

            'sin_foto_frente':
                Alumno.objects.filter(
                    Q(foto_frente__isnull=True) |
                    Q(foto_frente='')
                ).count(),

            'sin_foto_lado':
                Alumno.objects.filter(
                    Q(foto_lado__isnull=True) |
                    Q(foto_lado='')
                ).count(),

            'sin_foto_corte':
                Alumno.objects.filter(
                    Q(foto_corte__isnull=True) |
                    Q(foto_corte='')
                ).count(),
        }