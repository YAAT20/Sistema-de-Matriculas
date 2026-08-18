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
from django.contrib.auth.decorators import login_required, user_passes_test
from matriculas.views.admin import es_admin_check
from django.http import Http404, JsonResponse, HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
import io, zipfile, os
from django.utils.text import slugify
from django.views.decorators.http import require_POST
import json

@login_required
@user_passes_test(es_admin_check)
def dashboard(request):
    context = DashboardMarketingService.obtener_metricas()
    return render(request,'marketing/dashboard.html',context)

#eventos
@login_required
@user_passes_test(es_admin_check)
def eventos(request):
    eventos = EventoService.listar(q=request.GET.get('q'))
    return render(request,'marketing/eventos/lista.html',
        {'eventos': eventos}
    )

@login_required
@user_passes_test(es_admin_check)
def nuevo_evento(request):
    if request.method == 'POST':
        form = EventoForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Evento registrado correctamente.')
            return redirect('marketing:marketing_eventos')
    else:
        form = EventoForm()

    return render(request, 'marketing/eventos/formulario.html', {'form': form, 'evento': None})
    
@login_required
@user_passes_test(es_admin_check)
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

@login_required
@user_passes_test(es_admin_check)
def editar_evento(request, pk):

    evento = get_object_or_404(Evento,pk=pk)
    if request.method == 'POST':
        form = EventoForm(request.POST,request.FILES,instance=evento)
        if form.is_valid():
            form.save()
            messages.success(request,'Evento actualizado correctamente.')
            return redirect('marketing:marketing_evento',pk=evento.pk)

    else:

        form = EventoForm(instance=evento)

    return render(request,'marketing/eventos/formulario.html',{'form': form,'evento': evento}
    )

@login_required
@user_passes_test(es_admin_check)
def eliminar_evento(request, pk):
    evento = get_object_or_404(Evento, pk=pk)
    
    if request.method == 'POST':
        evento.delete()
        messages.success(request, 'Evento eliminado correctamente.')
        return redirect('marketing:marketing_eventos')
        
    return render(
        request, 
        'marketing/eventos/eliminar.html', 
        {'objeto': evento, 'tipo': 'evento'}
    )

@login_required
@user_passes_test(es_admin_check)
def fotos_evento(request, pk):
    evento = get_object_or_404(Evento.objects.prefetch_related('fotos'), pk=pk)

    if request.method == 'POST':
        archivos = request.FILES.getlist('imagenes')
        ultimo_orden = evento.fotos.order_by('-orden').values_list('orden', flat=True).first() or 0

        for indice, archivo in enumerate(archivos, start=1):
            foto = FotoEvento.objects.create(
                evento=evento, 
                imagen=archivo, 
                orden=ultimo_orden + indice
            )
            
            ThumbnailService.generar(foto)            
            foto.save()

        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'status': 'success', 'mensaje': f'{len(archivos)} archivos cargados correctamente.'})

        messages.success(request, f'{len(archivos)} archivos cargados correctamente.')
        return redirect('marketing:marketing_fotos_evento', pk=evento.pk)

    return render(request, 'marketing/eventos/fotos.html', {'evento': evento})

@login_required
@user_passes_test(es_admin_check)
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

@login_required
@user_passes_test(es_admin_check)
def descargar_todas_fotos(request, pk):
    """Empaqueta todas las fotos de un evento en un archivo .ZIP y lo descarga."""
    evento = get_object_or_404(Evento, pk=pk)
    fotos = evento.fotos.all()
    
    if not fotos:
        raise Http404("Este evento no tiene fotografías para descargar.")
        
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, 'w') as zip_file:
        for contador, foto in enumerate(fotos, start=1):
            try:
                nombre_archivo = os.path.basename(foto.imagen.name)
                extension = nombre_archivo.split('.')[-1] if '.' in nombre_archivo else 'jpg'
                nombre_en_zip = f"foto_{contador}.{extension}"
                zip_file.writestr(nombre_en_zip, foto.imagen.read())
            except Exception:
                continue
    buffer.seek(0)
    nombre_zip = f"fotos_{slugify(evento.nombre)}.zip"
    response = HttpResponse(buffer, content_type='application/zip')
    response['Content-Disposition'] = f'attachment; filename="{nombre_zip}"'
    
    return response

#ALCANCES
@login_required
@require_POST
def crear_alcance(request):
    try:
        data = json.loads(request.body)
        nombre = data.get('nombre', '').strip()

        if not nombre:
            return JsonResponse({'success': False, 'error': 'El nombre no puede estar vacío.'})

        alcance, created = Alcance.objects.get_or_create(
            nombre__iexact=nombre, 
            defaults={'nombre': nombre}
        )

        return JsonResponse({
            'success': True,
            'id': alcance.id,
            'nombre': alcance.nombre,
            'created': created
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@login_required
@require_POST
def editar_alcance(request, pk):
    try:
        data = json.loads(request.body)
        nuevo_nombre = data.get('nombre', '').strip()
        
        if not nuevo_nombre:
            return JsonResponse({'success': False, 'error': 'El nombre no puede estar vacío.'})
            
        alcance = get_object_or_404(Alcance, pk=pk)
        alcance.nombre = nuevo_nombre
        alcance.save()
        
        return JsonResponse({'success': True, 'id': alcance.id, 'nombre': alcance.nombre})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@login_required
@require_POST
def eliminar_alcance(request, pk):
    try:
        alcance = get_object_or_404(Alcance, pk=pk)
        alcance.delete()
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

#PUBLICACIONES
@login_required
@user_passes_test(es_admin_check)
def publicaciones(request):
    publicaciones = PublicacionService.listar()
    alcances_globales = list(Alcance.objects.values('id', 'nombre').order_by('nombre'))
    
    return render(
        request,
        "marketing/publicaciones/lista.html",
        {
            "publicaciones": publicaciones,
            "alcances_globales": alcances_globales,
        }
    )

@login_required
@user_passes_test(es_admin_check)
def publicacion(request, pk):

    publicacion = PublicacionService.obtener(pk)

    return render(request, 'marketing/publicaciones/detalle.html', {
        'publicacion': publicacion
    })

@login_required
@user_passes_test(es_admin_check)
def nueva_publicacion(request):
    if request.method == "POST":
        form = PublicacionForm(request.POST, request.FILES)
        publicacion = Publicacion()
        
        copy_formset = CopyFormSet(request.POST, instance=publicacion, prefix="copies")
        archivo_formset = ArchivoFormSet(request.POST, request.FILES, instance=publicacion, prefix="archivos")

        if form.is_valid() and copy_formset.is_valid() and archivo_formset.is_valid():
            with transaction.atomic():
                publicacion = PublicacionService.crear(
                    form=form,
                    copy_formset=copy_formset,
                    archivo_formset=archivo_formset
                )
            messages.success(request, "La publicación fue creada correctamente.")
            return redirect("marketing:marketing_publicacion", pk=publicacion.pk)

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

@login_required
@user_passes_test(es_admin_check)
def editar_publicacion(request, pk):
    publicacion = get_object_or_404(Publicacion, pk=pk)
    
    if request.method == "POST":
        form = PublicacionForm(request.POST, request.FILES, instance=publicacion)
        copy_formset = CopyFormSet(request.POST, instance=publicacion, prefix="copies")
        archivo_formset = ArchivoFormSet(request.POST, request.FILES, instance=publicacion, prefix="archivos")

        if form.is_valid() and copy_formset.is_valid() and archivo_formset.is_valid():
            with transaction.atomic():
                publicacion = PublicacionService.actualizar(
                    publicacion=publicacion,
                    form=form,
                    copy_formset=copy_formset,
                    archivo_formset=archivo_formset
                )

            messages.success(request, "La publicación fue actualizada correctamente.")
            return redirect("marketing:marketing_publicacion", pk=publicacion.pk)

    else:
        form = PublicacionForm(instance=publicacion)
        copy_formset = CopyFormSet(instance=publicacion, prefix="copies")
        archivo_formset = ArchivoFormSet(instance=publicacion, prefix="archivos")

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

@login_required
@user_passes_test(es_admin_check)
def eliminar_publicacion(request, pk):

    publicacion = PublicacionService.obtener(pk)

    if request.method == 'POST':
        PublicacionService.eliminar(publicacion)
        messages.success(request, 'Publicación eliminada')
        return redirect('marketing:marketing_publicaciones')

    return render(request, 'marketing/publicaciones/eliminar.html', {
        'publicacion': publicacion
    })

@login_required
@user_passes_test(es_admin_check)
def descargar_todos_archivos_publicacion(request, pk):
    """Empaqueta todas las imágenes y vídeos de una publicación en un archivo .ZIP."""
    # Cambia 'Publicacion' por el nombre real de tu modelo de publicación si es distinto
    publicacion = get_object_or_404(Publicacion, pk=pk) 
    archivos = publicacion.archivos.all()
    
    if not archivos:
        raise Http404("Esta publicación no tiene archivos multimedia para descargar.")
        
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, 'w') as zip_file:
        for contador, archivo_obj in enumerate(archivos, start=1):
            try:
                # Extraemos el nombre original del archivo físico en disco
                nombre_original = os.path.basename(archivo_obj.archivo.name)
                
                # Prevenimos colisiones de nombres o nombres vacíos
                if '.' in nombre_original:
                    extension = nombre_original.split('.')[-1].lower()
                else:
                    extension = 'jpg' # Valor por defecto
                
                nombre_en_zip = f"archivo_{contador}_{slugify(publicacion.titulo)[:20]}.{extension}"
                
                # Añadimos los bytes del archivo (sea .mp4, .png, etc.) al empaquetado zip
                zip_file.writestr(nombre_en_zip, archivo_obj.archivo.read())
            except Exception:
                continue

    buffer.seek(0)
    nombre_zip = f"recursos_{slugify(publicacion.titulo)[:40]}.zip"
    
    response = HttpResponse(buffer, content_type='application/zip')
    response['Content-Disposition'] = f'attachment; filename="{nombre_zip}"'
    
    return response

@login_required
@user_passes_test(es_admin_check)
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

    alumnos_con_fotos = []
    
    for alumno in alumnos:
        fotos_expediente = [
            ('Previa', alumno.foto_previa),
            ('Frente', alumno.foto_frente),
            ('Lado', alumno.foto_lado),
            ('Corte', alumno.foto_corte),
        ]

        lista_fotos_alumno = []
        urls_descarga = []
        
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

            lista_fotos_alumno.append({
                'tipo': tipo,
                'url': foto.url,
                'thumb_url': thumb_url
            })
            urls_descarga.append(foto.url)

        # Solo incluimos al alumno si posee al menos una fotografía registrada
        if lista_fotos_alumno:
            alumnos_con_fotos.append({
                'objeto': alumno,
                'fotos': lista_fotos_alumno,
                # Guardamos las URLs separadas por comas para leerlas fácil en JS
                'urls_combinadas': ",".join(urls_descarga), 
                'foto_principal': lista_fotos_alumno[0]['thumb_url']
            })

    context = {
        'alumnos': alumnos_con_fotos,
        'titulo': titulo,
        'grupo_actual': grupo_seleccionado,
        'q': q,
    }
    
    return render(request, 'marketing/alumnos/galeria.html', context)

@login_required
@user_passes_test(es_admin_check)
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

@login_required
@user_passes_test(es_admin_check)
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

@login_required
@user_passes_test(es_admin_check)
def eliminar_recurso(request, pk):
    """Elimina el registro de un recurso de manera directa."""
    recurso = get_object_or_404(RecursoMarketing, pk=pk)
    recurso.delete()
    messages.success(request, 'Recurso eliminado de la biblioteca.')
    return redirect('marketing:marketing_recursos')

@login_required
@user_passes_test(es_admin_check)
def descargar_recurso(request, pk):
    """Verifica permisos y redirige a la URL segura del archivo."""
    recurso = get_object_or_404(RecursoMarketing, pk=pk)
    
    if not recurso.archivo:
        raise Http404("El recurso no tiene un archivo asignado.")        
    return redirect(recurso.archivo.url)