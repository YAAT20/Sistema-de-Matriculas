import json
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
from matriculas.models import *
from django.shortcuts import render, redirect
from matriculas.forms import *
from django.contrib import messages
from django.db.models import Sum, F, Value, DecimalField, ExpressionWrapper, Q, Count
from django.utils import timezone
from matriculas.models import Matricula
from django.http import JsonResponse
from django.utils import timezone
from urllib.parse import quote
from django.db.models.functions import Coalesce
from matriculas.utils import *

@login_required
def lista_pagos_matricula(request, matricula_id):
    matricula = get_object_or_404(Matricula, id=matricula_id)
    pagos = matricula.pagos.order_by('numero_cuota', 'fecha_vencimiento')
    return render(request, 'matriculas/pagos/lista_pagos.html', {'matricula': matricula, 'pagos': pagos})

@login_required
def registrar_pago(request, matricula_id):
    matricula = get_object_or_404(Matricula, id=matricula_id)
    
    if request.method == 'POST':
        form = PagoForm(request.POST, request.FILES, user=request.user)
        if form.is_valid():
            nuevo_pago = form.save(commit=False)
            nuevo_pago.matricula = matricula
            nuevo_pago.usuario_registro = request.user
            nuevo_pago.save()
            messages.success(request, 'Pago registrado correctamente.')
            return redirect('matriculas:lista_pagos_matricula', matricula_id=matricula.id)
    else:
        form = PagoForm(user=request.user)
        
    return render(request, 'matriculas/pagos/formulario_pago.html', {'form': form, 'matricula': matricula})

@login_required
def editar_pago(request, pago_id):
    pago = get_object_or_404(Pago, id=pago_id)
    
    if request.method == 'POST':
        form = PagoForm(request.POST, request.FILES, instance=pago, user=request.user) 
        
        if form.is_valid():
            pago_editado = form.save(commit=False)

            if pago_editado.estado == 'pendiente':
                pago_editado.monto_pagado = 0
                pago_editado.fecha_pago = None

            pago_editado.save() 
            messages.success(request, 'Pago actualizado correctamente.')
            return redirect('matriculas:lista_pagos_matricula', matricula_id=pago.matricula.id)
    else:
        form = PagoForm(instance=pago, user=request.user)
        
    return render(request, 'matriculas/pagos/formulario_pago.html', {
        'form': form,
        'matricula': pago.matricula
    })

@login_required
def resumen_general_pagos(request):
    es_admin = request.user.is_authenticated and hasattr(request.user, 'perfil') and request.user.perfil.tipo == 'admin'

    estado_filter = request.GET.get('estado')
    search_query = request.GET.get('search')

    matriculas = Matricula.objects.select_related('alumno').annotate(
        total_pagos=Count('pagos'),
        cuotas_pagadas=Count('pagos', filter=Q(pagos__estado='pagado')),
        
        monto_total=Coalesce(Sum('pagos__monto_programado'), Value(0, output_field=DecimalField())),
        monto_pagado=Coalesce(Sum('pagos__monto_pagado'), Value(0, output_field=DecimalField())),
    ).annotate(
        deuda=ExpressionWrapper(
            F('monto_total') - F('monto_pagado'),
            output_field=DecimalField()
        )
    ).order_by('codigo')
    
    if search_query:
        matriculas = matriculas.filter(
            Q(alumno__nombres_completos__icontains=search_query) |
            Q(codigo__icontains=search_query) |
            Q(alumno__numero_whatsapp=search_query) |
            Q(apoderado__celular=search_query)
        )

    if estado_filter == 'completado':
        matriculas = matriculas.filter(cuotas_pagadas=F('total_pagos'), total_pagos__gt=0)
    
    elif estado_filter == 'parcial':
        matriculas = matriculas.filter(cuotas_pagadas__gt=0, cuotas_pagadas__lt=F('total_pagos'))
    
    elif estado_filter == 'sin_pagos':
        matriculas = matriculas.filter(cuotas_pagadas=0)

    if not es_admin:
        matriculas = matriculas.exclude(cuotas_pagadas=F('total_pagos'), total_pagos__gt=0)

    datos_globales = matriculas.aggregate(
        suma_deuda_total=Sum('deuda')
    )
    
    total_por_cobrar = datos_globales['suma_deuda_total'] or 0

    context = {
        'matriculas': matriculas,
        'total_por_cobrar': total_por_cobrar,
    }
    return render(request, 'matriculas/pagos/lista_general_pagos.html', context)

@login_required
def cobranza_vencidas_view(request):
    hoy = timezone.now().date()
    # Cuotas vencidas y Qque tovia no estan pagadas
    cuotas_vencidas = Pago.objects.filter(
        fecha_vencimiento__lt=hoy,
        estado='pendiente',
        tipo_pago='cuota'
    ).select_related('matricula__alumno', 'matricula__apoderado')

    # Agrupar por apoderado para reportes
    apoderados = {}
    for cuota in cuotas_vencidas:
        apoderado = cuota.matricula.apoderado
        if apoderado:
            if apoderado.id not in apoderados:
                apoderados[apoderado.id] = {
                    'apoderado': apoderado,
                    'cuotas': []
                }
            apoderados[apoderado.id]['cuotas'].append(cuota)

    context = {
        'cuotas_vencidas': cuotas_vencidas,
        'apoderados': apoderados.values(),
    }
    return render(request, 'matriculas/pagos/cobranzas_vencidas.html', context)

@login_required
def reporte_financiero_anual(request):
    anio_actual = timezone.now().year
    anio_consulta = int(request.GET.get('anio', anio_actual))
    
    pagos = Pago.objects.filter(
        fecha_vencimiento__year=anio_consulta,
        tipo_pago='cuota'
    )

    meses_data = []
    nombres_meses = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic']
    
    total_anual_programado = 0
    total_anual_pagado = 0
    total_anual_deuda = 0

    temp_prog = {m: 0 for m in range(1, 13)}
    temp_pag = {m: 0 for m in range(1, 13)}
    temp_deu = {m: 0 for m in range(1, 13)}

    for pago in pagos:
        mes = pago.fecha_vencimiento.month
        
        monto = pago.monto_programado
        temp_prog[mes] += monto
        total_anual_programado += monto

        if pago.estado == 'pagado':
            temp_pag[mes] += pago.monto_pagado
            total_anual_pagado += pago.monto_pagado
        else:
            pagado = pago.monto_pagado or 0
            temp_pag[mes] += pagado
            total_anual_pagado += pagado
            
            deuda = pago.monto_programado - pagado
            temp_deu[mes] += deuda
            total_anual_deuda += deuda

    tabla_mensual = []
    
    for i in range(1, 13):
        m_prog = temp_prog[i]
        m_pag = temp_pag[i]
        m_deu = temp_deu[i]

        pct_prog = (m_prog / total_anual_programado * 100) if total_anual_programado > 0 else 0
        pct_pag = (m_pag / total_anual_pagado * 100) if total_anual_pagado > 0 else 0
        pct_deu = (m_deu / total_anual_deuda * 100) if total_anual_deuda > 0 else 0

        tabla_mensual.append({
            'nombre': nombres_meses[i-1],
            'programado': {'monto': m_prog, 'pct': pct_prog},
            'pagado': {'monto': m_pag, 'pct': pct_pag},
            'deuda': {'monto': m_deu, 'pct': pct_deu},
        })

    context = {
        'anio_consulta': anio_consulta,
        'tabla_mensual': tabla_mensual,
        'totales': {
            'programado': total_anual_programado,
            'pagado': total_anual_pagado,
            'deuda': total_anual_deuda
        },
        'anios_disponibles': range(anio_actual - 2, anio_actual + 2),
    }
    
    return render(request, 'matriculas/admin/reporte_financiero.html', context)

##reporte devengado
@login_required
def reporte_financiero_devengado(request):
    anio_actual = timezone.now().year
    anio_consulta = int(request.GET.get('anio', anio_actual))
    
    pagos = Pago.objects.filter(
        matricula__fecha_matricula__year=anio_consulta,
        tipo_pago='cuota'
    ).select_related('matricula') 

    nombres_meses = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic']
    
    total_anual_programado = 0
    total_anual_pagado = 0
    total_anual_deuda = 0

    temp_prog = {m: 0 for m in range(1, 13)}
    temp_pag = {m: 0 for m in range(1, 13)}
    temp_deu = {m: 0 for m in range(1, 13)}

    for pago in pagos:
        mes = pago.matricula.fecha_matricula.month 
        
        monto = pago.monto_programado
        temp_prog[mes] += monto
        total_anual_programado += monto

        if pago.estado == 'pagado':
            temp_pag[mes] += pago.monto_pagado
            total_anual_pagado += pago.monto_pagado
        else:
            pagado = pago.monto_pagado or 0
            temp_pag[mes] += pagado
            total_anual_pagado += pagado
            
            deuda = pago.monto_programado - pagado
            temp_deu[mes] += deuda
            total_anual_deuda += deuda

    tabla_mensual = []
    
    for i in range(1, 13):
        m_prog = temp_prog[i]
        m_pag = temp_pag[i]
        m_deu = temp_deu[i]

        pct_prog = (m_prog / total_anual_programado * 100) if total_anual_programado > 0 else 0
        pct_pag = (m_pag / total_anual_pagado * 100) if total_anual_pagado > 0 else 0
        pct_deu = (m_deu / total_anual_deuda * 100) if total_anual_deuda > 0 else 0

        tabla_mensual.append({
            'nombre': nombres_meses[i-1],
            'programado': {'monto': m_prog, 'pct': pct_prog},
            'pagado': {'monto': m_pag, 'pct': pct_pag},
            'deuda': {'monto': m_deu, 'pct': pct_deu},
        })

    context = {
        'titulo_reporte': 'Reporte Comercial (Devengado)',
        'anio_consulta': anio_consulta,
        'tabla_mensual': tabla_mensual,
        'totales': {
            'programado': total_anual_programado,
            'pagado': total_anual_pagado,
            'deuda': total_anual_deuda
        },
        'anios_disponibles': range(anio_actual - 2, anio_actual + 2),
    }
    
    return render(request, 'matriculas/admin/reporte_devengado.html', context)

#PARA OBSERVAR CUOTAS, ETC ETC
@login_required
def api_seguimiento(request, matricula_id):
    if request.method == 'GET':
        eventos = Seguimiento.objects.filter(matricula_id=matricula_id).values(
            'texto', 'fecha_registro', 'usuario__username'
        )
        data = []
        for ev in eventos:
            fecha_local = timezone.localtime(ev['fecha_registro']) 
            
            data.append({
                'texto': ev['texto'],
                'usuario': ev['usuario__username'] or 'Sistema',
                'fecha': fecha_local.strftime("%d/%m %H:%M")
            })
        return JsonResponse({'eventos': data})

    if request.method == 'POST':
        data = json.loads(request.body)
        texto = data.get('texto', '').strip()
        
        if not texto:
            return JsonResponse({'error': 'Vacío'}, status=400)

        matricula = Matricula.objects.select_related(
            'alumno',
            'apoderado',
            'ciclo',
            'turno',
            'horario'
        ).get(id=matricula_id)

        nuevo = Seguimiento.objects.create(
            matricula=matricula,
            usuario=request.user,
            texto=texto
        )

        fecha_local = timezone.localtime(nuevo.fecha_registro)

        alumno = matricula.alumno

        resumen = (texto[:100] + '...') if len(texto) > 100 else texto

        titulo = "Nuevo seguimiento registrado"

        cuerpo = (
            f"{alumno.codigo} - {alumno.nombres_completos} | "
            f"{matricula.codigo} | "
            f"{request.user.username} {fecha_local.strftime('%d/%m %H:%M')} | "
            f"{resumen}"
        )

        notificar_admins_async(
            titulo=titulo,
            cuerpo=cuerpo,
            url_destino=f"/matriculas/detalle/{matricula.id}/",
            actor=request.user
        )

        return JsonResponse({
            'status': 'ok',
            'fecha': fecha_local.strftime("%d/%m %H:%M"),
            'usuario': nuevo.usuario.username
        })
    
#imprimir lista de cuotas
@login_required 
def imprimir_reporte_deudas(request):
    matriculas = Matricula.objects.select_related('alumno', 'apoderado').annotate(
        total_pagos=Count('pagos'),
        cuotas_pagadas=Count('pagos', filter=Q(pagos__estado='pagado')),
        monto_total=Coalesce(Sum('pagos__monto_programado'), Value(0, output_field=DecimalField())),
        monto_pagado=Coalesce(Sum('pagos__monto_pagado'), Value(0, output_field=DecimalField())),
    ).annotate(
        deuda=ExpressionWrapper(
            F('monto_total') - F('monto_pagado'),
            output_field=DecimalField()
        )
    ).order_by('alumno__codigo')

    matriculas = matriculas.filter(deuda__gt=0, total_pagos__gt=0)

    search_query = request.GET.get('search')
    if search_query:
        matriculas = matriculas.filter(
            Q(alumno__nombres_completos__icontains=search_query) |
            Q(codigo__icontains=search_query) |
            Q(alumno__numero_whatsapp=search_query) |
            Q(apoderado__celular=search_query)
        )

    datos_globales = matriculas.aggregate(
        total_deuda_reporte=Sum('deuda'),
        total_monto_reporte=Sum('monto_total')
    )

    context = {
        'matriculas': matriculas,
        'total_deuda': datos_globales['total_deuda_reporte'] or 0,
        'fecha_impresion': timezone.now(),
        'usuario_impresion': request.user
    }
    
    return render(request, 'matriculas/pagos/imprimir_deudas.html', context)

@login_required
def enviar_mensaje_cobranza_general(request, matricula_id, tipo_destinatario):
    # 1. Obtenemos la matrícula
    matricula = get_object_or_404(Matricula, id=matricula_id)
    
    # 2. Definimos a quién vamos a escribir y obtenemos sus datos
    if tipo_destinatario == 'alumno':
        persona = matricula.alumno
        nombre_destinatario = matricula.alumno.nombres_completos
        telefono = matricula.alumno.numero_whatsapp
        rol = "alumno"
    elif tipo_destinatario == 'apoderado':
        persona = matricula.apoderado
        if not persona:
            messages.error(request, "Esta matrícula no tiene apoderado registrado.")
            return redirect('matriculas:resumen_general_pagos')
        nombre_destinatario = matricula.apoderado.nombre_completo
        telefono = matricula.apoderado.celular
        rol = "apoderado"
    else:
        return redirect('matriculas:resumen_general_pagos')

    if not telefono:
        messages.error(request, f"El {rol} {nombre_destinatario} no tiene número registrado.")
        return redirect('matriculas:resumen_general_pagos')

    pagos_pendientes = matricula.pagos.filter(estado='pendiente')
    
    if not pagos_pendientes.exists():
        messages.success(request, f"¡Genial! El alumno {matricula.alumno.nombres_completos} está al día en sus pagos.")
        return redirect('matriculas:resumen_general_pagos')

    total_deuda = pagos_pendientes.aggregate(total=Sum('monto_programado'))['total'] or 0
    lista_cuotas = [str(p.numero_cuota) for p in pagos_pendientes if p.numero_cuota]
    texto_cuotas = ", ".join(lista_cuotas) if lista_cuotas else "pendientes"

    if tipo_destinatario == 'alumno':
        mensaje = (
            f"Hola *{nombre_destinatario}* 👋, te escribimos de la Academia.\n"
            f"Tienes pendiente el pago de tus cuotas: *{texto_cuotas}*.\n"
            f"💰 Monto total: *S/ {total_deuda:.2f}*.\n"
            f"Te agradeceríamos regularizarlo pronto."
        )
    else:
        mensaje = (
            f"Estimado(a) Sr(a). *{nombre_destinatario}*,\n"
            f"Le informamos que el alumno *{matricula.alumno.nombres_completos}* presenta pagos pendientes.\n"
            f"📝 Cuotas: {texto_cuotas}\n"
            f"💰 Deuda Total: *S/ {total_deuda:.2f}*\n"
            f"Agradeceremos su gestión para regularizarlo."
        )

    numero_limpio = telefono.replace(' ', '').replace('-', '').replace('+', '')
    if len(numero_limpio) == 9:
        numero_limpio = '51' + numero_limpio

    url = f"https://wa.me/{numero_limpio}?text={quote(mensaje)}"
    
    return redirect(url)