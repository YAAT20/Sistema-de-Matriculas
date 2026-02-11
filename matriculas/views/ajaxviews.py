from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
from matriculas.models import *
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.http import JsonResponse
#AJAX  
@login_required
def obtener_apoderado_por_alumno(request):
    alumno_id = request.GET.get('alumno_id')
    try:
        alumno = Alumno.objects.get(id=alumno_id)
        # Primero intentar obtener un apoderado asociado directamente al alumno (M2M)
        apoderado = alumno.apoderados.order_by('-id').first()
        if apoderado:
            return JsonResponse({
                'id': apoderado.id,
                'nombre': f"{apoderado.codigo} - {apoderado.nombre_completo}"
            })

        # Si no hay M2M, intentar obtener el apoderado desde la matrícula más reciente
        matricula = alumno.matriculas.select_related('apoderado').order_by('-id').first()
        if matricula and matricula.apoderado:
            apoderado = matricula.apoderado
            return JsonResponse({
                'id': apoderado.id,
                'nombre': f"{apoderado.codigo} - {apoderado.nombre_completo}"
            })
    except Alumno.DoesNotExist:
        pass
    return JsonResponse({}, status=404)

@login_required
def obtener_alumnos_por_apoderado(request):
    apoderado_id = request.GET.get('apoderado_id')
    try:
        apoderado = Apoderado.objects.get(id=apoderado_id)
        alumnos = apoderado.alumnos.all()
        data = [{
            'id': alumno.id,
            'nombre': f"{alumno.codigo} - {alumno.nombres_completos}"
        } for alumno in alumnos]
        return JsonResponse({'alumnos': data})
    except Apoderado.DoesNotExist:
        return JsonResponse({'alumnos': []})
    
@login_required
def todos_apoderados(request):
    apoderados = Apoderado.objects.all().values('id', 'nombre_completo')
    data = [{'id': a['id'], 'nombre': a['nombre_completo']} for a in apoderados]
    return JsonResponse({'apoderados': data})

@login_required
def todos_alumnos(request):
    alumnos = Alumno.objects.all().values('id', 'nombres_completos')
    data = [{'id': a['id'], 'nombre': a['nombres_completos']} for a in alumnos]
    return JsonResponse({'alumnos': data})

@login_required
def buscar_alumnos(request):
    q = request.GET.get('q', '')
    alumnos = Alumno.objects.filter(nombres_completos__icontains=q)[:20]
    data = [{'id': a.id, 'nombre': a.nombres_completos} for a in alumnos]
    return JsonResponse(data, safe=False)

@login_required
def buscar_apoderados(request):
    q = request.GET.get('q', '')
    apoderados = Apoderado.objects.filter(nombre_completo__icontains=q)[:20]
    data = [{'id': a.id, 'nombre': a.nombre_completo} for a in apoderados]
    return JsonResponse(data, safe=False)

@require_POST
@login_required
def confirmar_pago_ajax(request, pago_id):
    pago = get_object_or_404(Pago, id=pago_id, estado='pendiente')
    monto = pago.monto_programado
    fecha_actual = timezone.now().date()

    pago.confirmar_pago(monto_pagado=monto, usuario=request.user, fecha_pago=fecha_actual)

    return JsonResponse({
        'success': True,
        'fecha_pago': fecha_actual.strftime('%Y-%m-%d'),
        'monto_pagado': str(monto),
        'estado': pago.get_estado_display()
    })
