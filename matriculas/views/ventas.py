from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth.decorators import login_required           
from matriculas.models import Venta, VentaAlumno, Alumno
from django.views.decorators.http import require_POST

@login_required
def crear_venta(request):
    # siempre cargamos la lista de ventas activas para mostrar en el bloque derecho
    ventas = list(Venta.objects.filter(activo=True).order_by('-fecha'))
    # estadísticas básicas utilizadas en el listado
    total_precio = sum((v.precio_unitario for v in ventas), 0)
    precio_total = total_precio

    venta = None
    registros = None
    alumnos = None

    if request.method == "POST":
        codigo = request.POST.get("codigo") 
        descripcion = request.POST.get("descripcion")
        precio = request.POST.get("precio")

        venta = Venta.objects.create(
            codigo=codigo,
            descripcion=descripcion,
            precio_unitario=precio,
            activo=True
        )
        # preparar datos para mostrar el detalle en la misma plantilla
        registros = venta.ventas_alumnos.select_related('alumno').all()
        alumnos = Alumno.objects.all()
        # agregamos la venta recién creada a la lista para que aparezca también
        ventas.insert(0, venta)
        # recalcular estadísticas con la nueva venta al principio
        total_precio = sum((v.precio_unitario for v in ventas), 0)
        precio_total = total_precio

    context = {
        "ventas": ventas,
        "venta": venta,
        "registros": registros,
        "alumnos": alumnos,
        "total_precio": total_precio,
        "precio_total": precio_total,
    }
    return render(request, "matriculas/ventas/crear_venta.html", context)

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

    venta_alumno.pagado = True
    venta_alumno.save()

    return JsonResponse({"success": True})

@login_required
@require_POST
def marcar_entregado(request, id):
    venta_alumno = get_object_or_404(VentaAlumno, id=id)

    if not venta_alumno.venta.activo:
        return JsonResponse({"error": "Venta cerrada"}, status=400)

    venta_alumno.entregado = True
    venta_alumno.save()

    return JsonResponse({"success": True})

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