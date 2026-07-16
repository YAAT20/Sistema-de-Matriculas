from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.contrib.admin.views.decorators import staff_member_required
from matriculas.models import *
from matriculas.forms import *
from django.shortcuts import render, redirect
from django.contrib import messages
from django.db.models import Sum
from django.shortcuts import get_object_or_404
from django.contrib.auth.mixins import UserPassesTestMixin
from django.http import JsonResponse
import json
from django.core.paginator import Paginator
from pathlib import Path


# Vista para editar el template de WhatsApp
@staff_member_required
def editar_mensaje_whatsapp(request):
    config = MensajeWhatsAppConfig.objects.first()
    if not config:
        config = MensajeWhatsAppConfig.objects.create()
    if request.method == 'POST':
        form = MensajeWhatsAppConfigForm(request.POST, instance=config)
        if form.is_valid():
            form.save()
            messages.success(request, 'Mensaje de WhatsApp actualizado correctamente.')
            return redirect('matriculas:editar_mensaje_whatsapp')
    else:
        form = MensajeWhatsAppConfigForm(instance=config)
    return render(request, 'matriculas/admin/editar_mensaje_whatsapp.html', {'form': form})

@login_required
def dashboard_view(request):
    if getattr(request.user, 'perfil', None) and request.user.perfil.tipo == 'marketing':
        return redirect('marketing:marketing_dashboard')

    hoy = timezone.now().date()
    primer_dia_mes = hoy.replace(day=1)
    
    if hoy.month == 12:
        ultimo_dia_mes = hoy.replace(month=12, day=31)
    else:
        import calendar
        last_day = calendar.monthrange(hoy.year, hoy.month)[1]
        ultimo_dia_mes = hoy.replace(day=last_day)

    total_alumnos = Alumno.objects.filter(activo=True).count()
    matriculas_activas = Matricula.objects.filter(estado='activa').count()
    ciclo_actual = Ciclo.objects.filter(activo=True).order_by('-fecha_inicio').first()
    total_apoderados = Apoderado.objects.count()

    pagos_mes = Pago.objects.filter(
        fecha_pago__range=(primer_dia_mes, ultimo_dia_mes),
        estado='pagado'
    ).aggregate(total=Sum('monto_pagado'))['total'] or 0.00

    cuotas_proyectadas_mes = Pago.objects.filter(
        fecha_vencimiento__range=(primer_dia_mes, ultimo_dia_mes),
        tipo_pago='cuota'
    )
    total_cuotas_mes = cuotas_proyectadas_mes.count()
    total_monto_cuotas_mes = cuotas_proyectadas_mes.aggregate(total=Sum('monto_programado'))['total'] or 0.00

    deuda_acumulada_query = Pago.objects.filter(
        estado='pendiente',
        tipo_pago='cuota',
        fecha_vencimiento__lte=ultimo_dia_mes
    )

    total_cuotas_pendientes_global = deuda_acumulada_query.count()
    total_monto_cuotas_pendientes_global = deuda_acumulada_query.aggregate(total=Sum('monto_programado'))['total'] or 0.00

    context = {
        'total_alumnos': total_alumnos,
        'matriculas_activas': matriculas_activas,
        'pagos_mes': pagos_mes,
        'ciclo_actual': ciclo_actual.nombre if ciclo_actual else None,
        'total_apoderados': total_apoderados,

        'total_cuotas_mes': total_cuotas_mes,
        'total_monto_cuotas_mes': total_monto_cuotas_mes,
        
        'total_cuotas_pendientes_mes': total_cuotas_pendientes_global, 
        'total_monto_cuotas_pendientes_mes': total_monto_cuotas_pendientes_global,
    }
    
    return render(request, 'matriculas/home.html', context)

@login_required
def enviar_recordatorio_cobranza(request, apoderado_id):
    apoderado = get_object_or_404(Apoderado, id=apoderado_id)
    cuota = Pago.objects.filter(
        matricula__apoderado=apoderado,
        estado='pendiente',
        fecha_vencimiento__lt=timezone.now().date(),
        tipo_pago='cuota'
    ).order_by('fecha_vencimiento').first()
    if not cuota:
        messages.info(request, 'No hay cuotas vencidas para este apoderado.')
        return redirect('matriculas:cobranzas_vencidas')
    # Redirigir al enlace de WhatsApp generado
    return redirect(cuota.get_whatsapp_url())

def es_admin_check(user):
    return (
        user.is_authenticated
        and hasattr(user, 'perfil')
        and user.perfil.tipo in {'admin', 'marketing'}
    )

class SoloAdminMixin(UserPassesTestMixin):
    """Mixin para permitir acceso solo a usuarios admin en Vistas Basadas en Clases"""
    
    def test_func(self):
        return (
            self.request.user.is_authenticated
            and hasattr(self.request.user, 'perfil')
            and self.request.user.perfil.tipo in {'admin', 'marketing'}
        )

    def handle_no_permission(self):
        # Si no es admin, muestra mensaje y redirige
        messages.error(self.request, "Acceso denegado: No tienes permisos de administrador.")
        return redirect('matriculas:matricula_list')

@login_required
def registrar_token_fcm(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            nuevo_token = data.get('token')

            if not nuevo_token:
                return JsonResponse({'error': 'Token vacío'}, status=400)

            # Esto asegura que el token sea único, pero vinculado al usuario actual.
            # Si el token ya existía para otro usuario, se actualiza al usuario actual.
            FCMDevice.objects.update_or_create(
                token=nuevo_token,
                defaults={'user': request.user}
            )

            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)