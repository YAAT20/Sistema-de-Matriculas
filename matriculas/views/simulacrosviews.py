from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from matriculas.models import Simulacro, Matricula, AsistenciaSimulacro
from matriculas.forms import SimulacroForm

@login_required
def crear_simulacro(request):
    if request.method == 'POST':
        form = SimulacroForm(request.POST)
        if form.is_valid():
            simulacro = form.save() # Guarda el simulacro con el turno elegido 
            messages.success(request, f"Simulacro {simulacro.nombre} programado para el turno {simulacro.turno.nombre}.")
            return redirect('matriculas:lista_simulacros')
    else:
        form = SimulacroForm()
    return render(request, 'matriculas/simulacros/crear_simulacro.html', {'form': form})

@login_required
def lista_simulacros(request):
    from django.utils import timezone
    simulacros = Simulacro.objects.all().order_by('-fecha')
    today = timezone.now().date()

    # Calcular estadísticas
    total_simulacros = simulacros.count()
    proximos = simulacros.filter(fecha__gt=today).count()
    hoy = simulacros.filter(fecha=today).count()
    pasados = simulacros.filter(fecha__lt=today).count()

    return render(request, 'matriculas/simulacros/lista_simulacros.html', {
        'simulacros': simulacros,
        'today': today,
        'total_simulacros': total_simulacros,
        'proximos': proximos,
        'hoy': hoy,
        'pasados': pasados,
    })

@login_required
def gestionar_simulacro(request, simulacro_id):
    simulacro = get_object_or_404(Simulacro, id=simulacro_id)
    
    if request.method == 'POST' and 'cargar_alumnos' in request.POST:
        matriculas = Matricula.objects.filter(
            ciclo=simulacro.ciclo, 
            turno=simulacro.turno, 
            estado='activa'
        )
        
        count = 0
        for mat in matriculas:
            obj, created = AsistenciaSimulacro.objects.get_or_create(
                simulacro=simulacro, 
                matricula=mat
            )
            if created:
                count += 1
        
        messages.success(request, f"Se cargaron {count} alumnos del turno {simulacro.turno.nombre}.")
        return redirect('matriculas:gestionar_simulacro', simulacro_id=simulacro.id)

    if request.method == 'POST' and 'guardar_asistencia' in request.POST:
        actualizado = 0
        errores = 0
        
        for key, value in request.POST.items():
            if key.startswith('pago_'):
                try:
                    asistencia_id = key.replace('pago_', '')
                    # Verificar que el valor es válido
                    valores_validos = ['no_dio', 'si', 'fondo', 'debe']
                    if value not in valores_validos:
                        errores += 1
                        continue
                    
                    result = AsistenciaSimulacro.objects.filter(id=asistencia_id).update(pago=value)
                    if result > 0:
                        actualizado += 1
                except Exception as e:
                    print(f"Error al actualizar asistencia {asistencia_id}: {str(e)}")
                    errores += 1
        
        if actualizado > 0:
            messages.success(request, f"Pago(s) actualizado(s) correctamente.")
        if errores > 0:
            messages.warning(request, f"⚠️ {errores} error(es) al actualizar.")
        if actualizado == 0 and errores == 0:
            messages.info(request, "No hay cambios para guardar.")
        
        return redirect('matriculas:gestionar_simulacro', simulacro_id=simulacro.id)

    asistencias = simulacro.asistencias.all().select_related('matricula__alumno').order_by('matricula__alumno__codigo')
    
    context = {
        'simulacro': simulacro,
        'asistencias': asistencias,
    }
    return render(request, 'matriculas/simulacros/gestionar_simulacro.html', context)