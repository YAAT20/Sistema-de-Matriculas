from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
from matriculas.models import *
from matriculas.utils import *
from django.http import JsonResponse
from django.views.decorators.http import require_POST
import json
from urllib.parse import quote
import urllib.parse
from django.utils import timezone

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

##ESTA ES LA VISTA PARA VER Y PAGAR LAS CUOTAS DE UN ALUMNO EN PARTICULAR
@require_POST
@login_required
def confirmar_pago_ajax(request, pago_id):
    try:
        data = json.loads(request.body)
        forma_pago = data.get('forma_pago', 'Efectivo')
        observacion = data.get('observacion', '').strip()
        pago_obj = get_object_or_404(Pago, id=pago_id)
        
        pago_obj.confirmar_pago(
            monto_pagado=pago_obj.monto_programado,
            usuario=request.user,
            forma_pago=forma_pago,
            observacion=observacion
        )

        ahora = timezone.localtime(timezone.now())
        pago_obj.fecha_confirmacion = ahora
        pago_obj.fecha_pago = ahora.date()
        pago_obj.save(update_fields=['fecha_confirmacion','fecha_pago'])
        
        notificar_admins_async(
            titulo="💰 Nuevo Pago Confirmado",
            cuerpo=(
                f"{request.user.username} registró "
                f"S/ {pago_obj.monto_programado} "
                f"de la matrícula #{pago_obj.matricula.id}."
            ),
            url_destino="/matriculas/pagos/",
            actor=request.user
        )

        alumno = pago_obj.matricula.alumno
        alumno_nombre = alumno.nombres_completos
        codigo_alumno = alumno.codigo
        cuota_str = (str(pago_obj.numero_cuota)
            if pago_obj.numero_cuota
            else "Única"
        )

        monto_str = str(pago_obj.monto_programado)
        usuario_registro = request.user.username
        fecha_pago = pago_obj.fecha_pago.strftime("%d/%m/%Y")
        hora_pago = timezone.localtime(pago_obj.fecha_confirmacion).strftime("%H:%M").lstrip("0")

        if pago_obj.boleta_sunat and pago_obj.boleta_sunat.name:
            if pago_obj.cod_boleta_sunat:
                estado_boleta = f"✅ Generada y subida ({pago_obj.cod_boleta_sunat})"
            else:
                estado_boleta = "✅ Generada y subida"
        else:
            estado_boleta = "⏳ Pendiente de emisión"

        return JsonResponse({
            'success': True,
            'whatsapp': {
                'numero': '51939824522',
                'alumno': alumno_nombre,
                'codigo_alumno': codigo_alumno,
                'cuota': cuota_str,
                'monto': monto_str,
                'forma_pago': forma_pago,
                'fecha_pago': fecha_pago,
                'hora_pago': hora_pago,
                'usuario': usuario_registro,
                'observacion': observacion,
                'estado_boleta': estado_boleta,
                'cod_boleta_sunat': pago_obj.cod_boleta_sunat or '-'
            }
        })

    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Los datos enviados no tienen un formato JSON válido.'
        }, status=400)

    except Exception as e:
        import traceback
        print("⚠️ ERROR EN CONFIRMAR PAGO:")
        traceback.print_exc()
        
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

@login_required
def obtener_datos_whatsapp_pago(request, pago_id):
    try:
        pago_obj = get_object_or_404(Pago, id=pago_id)
        
        alumno = pago_obj.matricula.alumno
        cuota_str = str(pago_obj.numero_cuota) if pago_obj.numero_cuota else "Única"
        
        if pago_obj.boleta_sunat and pago_obj.boleta_sunat.name:
            if pago_obj.cod_boleta_sunat:
                estado_boleta = f"✅ Generada-Cod:({pago_obj.cod_boleta_sunat})"
            else:
                estado_boleta = "✅ Generada y subida"
        else:
            estado_boleta = "⏳ Pendiente de emisión"
            
        fecha_pago = pago_obj.fecha_pago.strftime("%d/%m/%Y") if pago_obj.fecha_pago else "-"
        hora_pago = timezone.localtime(pago_obj.fecha_confirmacion).strftime("%H:%M").lstrip("0") if pago_obj.fecha_confirmacion else "-"
        usuario_registro = pago_obj.usuario_registro.username if pago_obj.usuario_registro else "-"

        return JsonResponse({
            'success': True,
            'whatsapp': {
                'numero': '51939824522',
                'alumno': alumno.nombres_completos,
                'codigo_alumno': alumno.codigo,
                'cuota': cuota_str,
                'monto': str(pago_obj.monto_programado),
                'forma_pago': pago_obj.forma_pago or 'Efectivo',
                'fecha_pago': fecha_pago,
                'hora_pago': hora_pago,
                'usuario': usuario_registro,
                'observacion': pago_obj.observacion,
                'estado_boleta': estado_boleta,
                'cod_boleta_sunat': pago_obj.cod_boleta_sunat or '-'
            }
        })
    except Exception as e:
        import traceback
        print("⚠️ ERROR AL REENVIAR WHATSAPP:")
        traceback.print_exc()
        
        return JsonResponse({'success': False, 'error': str(e)}, status=500)