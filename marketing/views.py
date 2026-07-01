from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from marketing.forms import *
from marketing.models import Evento, FotoEvento, Publicacion, RecursoMarketing
from marketing.services.dashboard import DashboardMarketingService
from marketing.services.eventos import EventoService
from marketing.services.publicaciones import PublicacionService
from matriculas.models import Alumno
from django.db.models import Q
from pathlib import Path
from django.db import transaction

def dashboard(request):
    context = DashboardMarketingService.obtener_metricas()
    return render(request,'marketing/dashboard.html',context)

#eventos
def eventos(request):
    eventos = EventoService.listar(q=request.GET.get('q'))
    return render(request,'marketing/eventos/lista.html',
        {'eventos': eventos}
    )

def nuevo_evento(request):
    if request.method == 'POST':

        form = EventoForm( request.POST)
        if form.is_valid():

            form.save()
            messages.success(
                request,
                'Evento registrado correctamente.'
            )
            return redirect(
                'marketing:marketing_eventos'
            )
    else:
        form = EventoForm()
    return render(
        request,
        'marketing/eventos/formulario.html',
        {
            'form': form,
            'evento': None
        }
    )

def evento(request, pk):
    evento = get_object_or_404(
        Evento.objects.prefetch_related(
            'fotos',
            'publicaciones'
        ),
        pk=pk
    )
    return render(request,'marketing/eventos/detalle.html',
        {'evento': evento}
    )

def editar_evento(request, pk):

    evento = get_object_or_404(
        Evento,
        pk=pk
    )

    if request.method == 'POST':

        form = EventoForm(
            request.POST,
            request.FILES,
            instance=evento
        )

        if form.is_valid():

            form.save()

            messages.success(
                request,
                'Evento actualizado correctamente.'
            )

            return redirect(
                'marketing:marketing_evento',
                pk=evento.pk
            )

    else:

        form = EventoForm(
            instance=evento
        )

    return render(
        request,
        'marketing/eventos/formulario.html',
        {
            'form': form,
            'evento': evento
        }
    )

def eliminar_evento(request, pk):
    evento = get_object_or_404(Evento, pk=pk)
    
    if request.method == 'POST':
        evento.delete()
        messages.success(request, 'Evento eliminado correctamente.')
        return redirect('marketing:marketing_eventos')
        
    return render(
        request, 
        'marketing/eventos/confirmar_eliminar.html', 
        {'objeto': evento, 'tipo': 'evento'}
    )

def fotos_evento(request, pk):

    evento = get_object_or_404(
        Evento.objects.prefetch_related('fotos'),
        pk=pk
    )
    if request.method == 'POST':

        archivos = request.FILES.getlist('imagenes')

        ultimo_orden = (
            evento.fotos
            .order_by('-orden')
            .values_list('orden', flat=True)
            .first()
        ) or 0

        for indice, archivo in enumerate(archivos, start=1):

            FotoEvento.objects.create(
                evento=evento,
                imagen=archivo,
                orden=ultimo_orden + indice
            )

        messages.success(
            request,
            f'{len(archivos)} fotos cargadas correctamente.'
        )

        return redirect(
            'marketing:marketing_fotos_evento',
            pk=evento.pk
        )

    return render(
        request,
        'marketing/eventos/fotos.html',
        {
            'evento': evento
        }
    )

def eliminar_foto_evento(request, pk):

    evento_id = EventoService.eliminar_foto(
        pk
    )
    messages.success(
        request,
        'Fotografía eliminada correctamente.'
    )
    return redirect(
        'marketing:marketing_fotos_evento',
        pk=evento_id
    )

#PUBLICACIONES
def publicaciones(request):

    publicaciones = PublicacionService.listar()
    return render(
        request,
        "marketing/publicaciones/lista.html",
        {"publicaciones": publicaciones}
    )

def publicacion(request, pk):

    publicacion = PublicacionService.obtener(pk)

    return render(request, 'marketing/publicaciones/detalle.html', {
        'publicacion': publicacion
    })

def nueva_publicacion(request):

    if request.method == "POST":

        form = PublicacionForm(request.POST, request.FILES)

        # instancia vacía para los formsets
        publicacion = Publicacion()

        copy_formset = CopyFormSet(
            request.POST,
            instance=publicacion,
            prefix="copies"
        )

        archivo_formset = ArchivoFormSet(
            request.POST,
            request.FILES,
            instance=publicacion,
            prefix="archivos"
        )

        if (
            form.is_valid()
            and copy_formset.is_valid()
            and archivo_formset.is_valid()
        ):

            with transaction.atomic():

                publicacion = PublicacionService.crear(
                    form=form,
                    copy_formset=copy_formset,
                    archivo_formset=archivo_formset
                )

            messages.success(request,"La publicación fue creada correctamente.")

            return redirect("marketing:marketing_publicacion",pk=publicacion.pk)

    else:
        form = PublicacionForm()
        copy_formset = CopyFormSet(prefix="copies")
        archivo_formset = ArchivoFormSet(prefix="archivos")

    return render(
        request,
        "marketing/publicaciones/formulario.html",
        {
            "form": form,
            "copy_formset": copy_formset,
            "archivo_formset": archivo_formset,
        }
    )

def editar_publicacion(request, pk):

    publicacion = get_object_or_404(
        Publicacion,
        pk=pk
    )

    if request.method == "POST":

        form = PublicacionForm(
            request.POST,
            request.FILES,
            instance=publicacion
        )

        copy_formset = CopyFormSet(
            request.POST,
            instance=publicacion,
            prefix="copies"
        )

        archivo_formset = ArchivoFormSet(
            request.POST,
            request.FILES,
            instance=publicacion,
            prefix="archivos"
        )

        if (
            form.is_valid()
            and copy_formset.is_valid()
            and archivo_formset.is_valid()
        ):

            with transaction.atomic():

                publicacion = PublicacionService.actualizar(
                    publicacion=publicacion,
                    form=form,
                    copy_formset=copy_formset,
                    archivo_formset=archivo_formset
                )

            messages.success(request,"La publicación fue actualizada correctamente.")
            return redirect("marketing:marketing_publicacion",pk=publicacion.pk)

    else:
        form = PublicacionForm(instance=publicacion)
        copy_formset = CopyFormSet(instance=publicacion,prefix="copies")
        archivo_formset = ArchivoFormSet(instance=publicacion,prefix="archivos")

    return render(
        request,
        "marketing/publicaciones/formulario.html",
        {
            "publicacion": publicacion,
            "form": form,
            "copy_formset": copy_formset,
            "archivo_formset": archivo_formset,
        }
    )

def eliminar_publicacion(request, pk):

    publicacion = PublicacionService.obtener(pk)

    if request.method == 'POST':
        PublicacionService.eliminar(publicacion)
        messages.success(request, 'Publicación eliminada')
        return redirect('marketing:marketing_publicaciones')

    return render(request, 'marketing/publicaciones/eliminar.html', {
        'publicacion': publicacion
    })

def recursos(request):

    recursos = RecursoMarketing.objects.all()

    return render(
        request,
        'marketing/recursos/lista.html',
        {
            'recursos': recursos
        }
    )

def galeria_alumnos(request):
    grupo_seleccionado = request.GET.get('grupo', 'pre5')
    q = request.GET.get('q', '').strip()

    alumnos = Alumno.objects.all()

    if grupo_seleccionado == 'pre5':
        alumnos = alumnos.filter(grado_estudios__in=['pre', '5s'])
        titulo = 'Pre y 5to'
    elif grupo_seleccionado == '34':
        alumnos = alumnos.filter(grado_estudios__in=['3s', '4s'])
        titulo = '3ro y 4to'
    else:
        alumnos = alumnos.filter(grado_estudios__in=['1s', '2s'])
        titulo = '1ro y 2do'

    if q:
        alumnos = alumnos.filter(
            Q(nombres_completos__icontains=q) | Q(codigo__icontains=q)
        )

    total_resultados = alumnos.count()

    fotos = []
    for alumno in alumnos:
        fotos_expediente = [
            ('Previa', alumno.foto_previa),
            ('Frente', alumno.foto_frente),
            ('Lado', alumno.foto_lado),
            ('Corte', alumno.foto_corte),
        ]

        for tipo, foto in fotos_expediente:
            if not foto:
                continue

            thumb_url = foto.url
            try:
                ruta = Path(foto.path)
                thumb = ruta.with_name(ruta.stem + '_thumb.jpg')

                if thumb.exists():
                    nombre_thumb = Path(foto.name).stem + '_thumb.jpg'
                    thumb_url = Path(foto.url).parent.as_posix() + '/' + nombre_thumb
            except Exception:
                pass

            fotos.append({
                'alumno': alumno,
                'tipo': tipo,
                'url': foto.url,
                'thumb_url': thumb_url,
            })

    context = {
        'fotos': fotos,
        'titulo': titulo,
        'grupo_actual': grupo_seleccionado,
        'q': q,
        'total_resultados': total_resultados,
    }
    
    return render(request, 'marketing/alumnos/galeria.html', context)

def recursos(request):
    """Lista todos los recursos permanentes permitiendo filtrar por categoría."""
    recursos_list = RecursoMarketing.objects.all()
    categoria_filtro = request.GET.get('categoria', '').strip()
    
    if categoria_filtro:
        recursos_list = recursos_list.filter(categoria=categoria_filtro)
        
    return render(
        request,
        'marketing/recursos/lista.html',
        {
            'recursos': recursos_list,
            'categoria_actual': categoria_filtro,
            'categorias': RecursoMarketing.CATEGORIAS
        }
    )

def nuevo_recurso(request):
    """Permite subir un nuevo archivo a la biblioteca de recursos."""
    if request.method == 'POST':
        form = RecursoMarketingForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, 'Recurso guardado correctamente en la biblioteca.')
            return redirect('marketing:marketing_recursos')
    else:
        form = RecursoMarketingForm()
        
    return render(request, 'marketing/recursos/formulario.html', {'form': form})

def eliminar_recurso(request, pk):
    """Elimina el registro de un recurso de manera directa."""
    recurso = get_object_or_404(RecursoMarketing, pk=pk)
    recurso.delete()
    messages.success(request, 'Recurso eliminado de la biblioteca.')
    return redirect('marketing:marketing_recursos')

def descargar_recurso(request, pk):
    """Fuerza la descarga del archivo multimedia en el navegador."""
    recurso = get_object_or_404(RecursoMarketing, pk=pk)
    try:
        response = FileResponse(recurso.archivo.open(), as_attachment=True)
        return response
    except Exception:
        raise Http404("El archivo no se encuentra físicamente en el servidor.")