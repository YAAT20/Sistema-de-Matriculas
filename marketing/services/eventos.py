from marketing.models import Evento
from marketing.models import FotoEvento
class EventoService:

    @staticmethod
    def listar(q=None):

        queryset = Evento.objects.select_related(
        )

        if q:
            queryset = queryset.filter(
                nombre__icontains=q
            )

        return queryset

    @staticmethod
    def obtener(pk):

        return Evento.objects.select_related(
        ).prefetch_related(
            'fotos',
            'publicaciones'
        ).get(
            pk=pk
        )
    
    @staticmethod
    def eliminar_foto(foto_id):

        foto = FotoEvento.objects.get(
            pk=foto_id
        )

        evento_id = foto.evento_id

        foto.delete()

        return evento_id