from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from ..models import *
from ..forms import ProcedimientoForm, PasoFormSet
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST

# CREATE
@login_required
def crear_procedimiento(request):
    if request.method == 'POST':
        form = ProcedimientoForm(request.POST)
        pasos_formset = PasoFormSet(request.POST, request.FILES, prefix='pasos')

        if form.is_valid() and pasos_formset.is_valid():
            procedimiento = form.save(commit=False)
            procedimiento.creado_por = request.user
            procedimiento.save()

            pasos = pasos_formset.save(commit=False)

            for i, paso in enumerate(pasos, start=1):
                paso.procedimiento = procedimiento
                paso.orden = i
                paso.save()

            return redirect('matriculas:lista_procedimientos')
    else:
        form = ProcedimientoForm()
        pasos_formset = PasoFormSet(prefix='pasos')

    return render(request, 'matriculas/procedimientos/crear.html', {
        'form': form,
        'pasos_formset': pasos_formset
    })

# LISTA
@login_required
def lista_procedimientos(request):
    procedimientos = Procedimiento.objects.filter(activo=True)
    return render(request, 'matriculas/procedimientos/lista.html', {
        'procedimientos': procedimientos
    })

# VER
@login_required
def ver_procedimiento(request, id):
    procedimiento = get_object_or_404(Procedimiento, id=id)
    return render(request, 'matriculas/procedimientos/ver.html', {
        'procedimiento': procedimiento
    })

# EDITAR
@login_required
def editar_procedimiento(request, id):
    procedimiento = get_object_or_404(Procedimiento, id=id)

    if request.method == 'POST':
        form = ProcedimientoForm(request.POST, instance=procedimiento)
        pasos_formset = PasoFormSet(request.POST, request.FILES, instance=procedimiento, prefix='pasos')

        if form.is_valid() and pasos_formset.is_valid():
            form.save()

            pasos = pasos_formset.save(commit=False)

            for obj in pasos_formset.deleted_objects:
                obj.delete()

            for i, paso in enumerate(pasos, start=1):
                paso.procedimiento = procedimiento
                paso.orden = i
                paso.save()
        
            return redirect('matriculas:ver_procedimiento', id=procedimiento.id)

    else:
        form = ProcedimientoForm(instance=procedimiento)
        pasos_formset = PasoFormSet(instance=procedimiento, prefix='pasos')

    return render(request, 'matriculas/procedimientos/editar.html', {
        'form': form,
        'pasos_formset': pasos_formset,
        'procedimiento': procedimiento
    })

# DELETE AJAX
@require_POST
@login_required
def eliminar_procedimiento_ajax(request, id):
    if request.method == 'POST':
        procedimiento = get_object_or_404(Procedimiento, id=id)
        procedimiento.activo = False
        procedimiento.save()
        return JsonResponse({'ok': True})

    return JsonResponse({'ok': False})