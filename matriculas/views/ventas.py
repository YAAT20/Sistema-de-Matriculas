from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth.decorators import login_required           
from matriculas.models import Venta, VentaAlumno, Alumno
from django.views.decorators.http import require_POST
from django.urls import reverse

@login_required
def crear_venta(request):
    if request.method == "POST":
        codigo = request.POST.get("codigo") 
        descripcion = request.POST.get("descripcion")
        precio = request.POST.get("precio")

        try:
            venta = Venta.objects.create(
                codigo=codigo,
                descripcion=descripcion,
                precio_unitario=precio,
                activo=True
            )
            
            # Si la petición es AJAX, respondemos con JSON
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({
                    "success": True,
                    "codigo": venta.codigo,
                    "descripcion": venta.descripcion,
                    "precio": str(venta.precio_unitario),
                    "url_detalle": reverse('matriculas:detalle_venta', args=[venta.id])
                })
            
            # Si no es AJAX (fallback), sigue normal
            return redirect('matriculas:crear_venta')
            
        except Exception as e:
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({"success": False, "error": str(e)}, status=400)

    # Para el método GET, cargamos las ventas existentes
    ventas = Venta.objects.filter(activo=True).order_by('-fecha')
    
    context = {
        "ventas": ventas,
    }
    return render(request, "matriculas/ventas/crear_venta.html", context)

@login_required
def seguimiento_pagos_alumno(request):
    # Ordenamos por nombres para que sea fácil buscarlos en la lista
    alumnos = Alumno.objects.filter(activo=True).order_by('codigo')
    alumno_seleccionado = None
    registros = []
    total_deuda = 0

    alumno_id = request.GET.get('alumno_id')
    if alumno_id:
        alumno_seleccionado = get_object_or_404(Alumno, id=alumno_id)
        registros = VentaAlumno.objects.filter(alumno=alumno_seleccionado).select_related('venta')
        # Calculamos la deuda sumando los que pagado=False
        total_deuda = sum(r.total for r in registros if not r.pagado)

    context = {
        "alumnos": alumnos,
        "alumno_seleccionado": alumno_seleccionado,
        "registros": registros,
        "total_deuda": total_deuda,
    }
    return render(request, "matriculas/ventas/seguimiento_alumno.html", context)

@login_required
@require_POST
def editar_observacion(request, id):
    registro = get_object_or_404(VentaAlumno, id=id)
    observacion = request.POST.get("observacion", "")
    registro.observacion = observacion
    registro.save()
    return JsonResponse({"success": True, "observacion": observacion})

@login_required
def agregar_alumno_venta(request, venta_id):
    venta = get_object_or_404(Venta, id=venta_id)

    if not venta.activo:
        return JsonResponse({"error": "Venta cerrada"}, status=400)

    if request.method != "POST":
        return JsonResponse({"error": "Método no permitido"}, status=405)

    alumno_id = request.POST.get("alumno")
    cantidad = request.POST.get("cantidad")
    observacion = request.POST.get("observacion", "") 

    if not alumno_id:
        return JsonResponse({"error": "Alumno requerido"}, status=400)

    alumno = get_object_or_404(Alumno, id=alumno_id)

    try:
        cantidad = int(cantidad)
        if cantidad <= 0:
            raise ValueError
    except (ValueError, TypeError):
        return JsonResponse({"error": "Cantidad inválida"}, status=400)

    if VentaAlumno.objects.filter(venta=venta, alumno=alumno).exists():
        return JsonResponse({"error": "Alumno ya registrado"}, status=400)

    venta_alumno = VentaAlumno.objects.create(
        venta=venta,
        alumno=alumno,
        cantidad=cantidad,
        observacion=observacion
    )

    return JsonResponse({
        "success": True,
        "id": venta_alumno.id,
        "alumno": venta_alumno.alumno.nombres_completos,
        "cantidad": venta_alumno.cantidad,
        "total": venta_alumno.total, 
        "observacion": venta_alumno.observacion
    })

@login_required
@require_POST
def marcar_pagado(request, id):
    venta_alumno = get_object_or_404(VentaAlumno, id=id)

    if not venta_alumno.venta.activo:
        return JsonResponse({"error": "Venta cerrada"}, status=400)

    venta_alumno.pagado = not venta_alumno.pagado
    venta_alumno.save()

    return JsonResponse({"success": True, "estado_actual": venta_alumno.pagado})

@login_required
@require_POST
def marcar_entregado(request, id):
    venta_alumno = get_object_or_404(VentaAlumno, id=id)

    if not venta_alumno.venta.activo:
        return JsonResponse({"error": "Venta cerrada"}, status=400)

    venta_alumno.entregado = not venta_alumno.entregado
    venta_alumno.save()

    return JsonResponse({"success": True, "estado_actual": venta_alumno.entregado})


@login_required
@require_POST
def eliminar_registro(request, id):
    venta_alumno = get_object_or_404(VentaAlumno, id=id)

    if not venta_alumno.venta.activo:
        return JsonResponse({"error": "Venta cerrada"}, status=400)

    venta_alumno.delete()

    return JsonResponse({"success": True})

@login_required
def detalle_venta(request, venta_id):
    venta = get_object_or_404(Venta, id=venta_id)
    registros = venta.ventas_alumnos.select_related('alumno').all()
    alumnos = Alumno.objects.all()
    
    context = {
        "venta": venta,
        "registros": registros,
        "alumnos": alumnos
    }
    return render(request, "matriculas/ventas/detalle_venta.html", context)