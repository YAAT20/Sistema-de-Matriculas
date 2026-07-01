from django.urls import Resolver404, resolve
from django.urls import reverse

from .models import Alumno, Apoderado, Matricula, Ciclo, Turno, Horario


def breadcrumb(request):
    """Agrega un breadcrumb simple según la ruta actual."""
    try:
        resolver_match = getattr(request, 'resolver_match', None) or resolve(request.path)
    except Resolver404:
        return {'breadcrumb': []}

    route_name = resolver_match.url_name
    kwargs = resolver_match.kwargs or {}

    items = [{'titulo': 'Inicio', 'url': reverse('matriculas:home')}]

    if not route_name or route_name in {'home', 'dashboard'}:
        return {'breadcrumb': [{'titulo': 'Inicio', 'url': None}]}

    def add_item(title, url=None):
        items.append({'titulo': title, 'url': url})

    if route_name in {'alumno_list', 'alumno_total_list'}:
        add_item('Alumnos', None)
    elif route_name == 'alumno_create':
        add_item('Alumnos', reverse('matriculas:alumno_list'))
        add_item('Registrar', None)
    elif route_name == 'alumno_detail':
        alumno = Alumno.objects.filter(pk=kwargs.get('pk')).first()
        add_item('Alumnos', reverse('matriculas:alumno_list'))
        add_item(alumno.nombres_completos if alumno else 'Detalle', None)
    elif route_name == 'alumno_update':
        add_item('Alumnos', reverse('matriculas:alumno_list'))
        add_item('Editar', None)

    elif route_name in {'apoderado_list'}:
        add_item('Apoderados', None)
    elif route_name == 'apoderado_create':
        add_item('Apoderados', reverse('matriculas:apoderado_list'))
        add_item('Registrar', None)
    elif route_name == 'apoderado_detail':
        apoderado = Apoderado.objects.filter(pk=kwargs.get('pk')).first()
        add_item('Apoderados', reverse('matriculas:apoderado_list'))
        add_item(apoderado.nombre_completo if apoderado else 'Detalle', None)
    elif route_name == 'apoderado_update':
        add_item('Apoderados', reverse('matriculas:apoderado_list'))
        add_item('Editar', None)

    elif route_name in {'matricula_list'}:
        add_item('Matrículas', None)
    elif route_name == 'matricula_create':
        add_item('Matrículas', reverse('matriculas:matricula_list'))
        add_item('Registrar', None)
    elif route_name == 'matricula_detail':
        matricula = Matricula.objects.filter(pk=kwargs.get('pk')).first()
        add_item('Matrículas', reverse('matriculas:matricula_list'))
        add_item('Detalle' if not matricula else matricula.codigo, None)
    elif route_name == 'matricula_update':
        add_item('Matrículas', reverse('matriculas:matricula_list'))
        add_item('Editar', None)

    elif route_name in {'ciclo_list', 'turno_list', 'horario_list'}:
        add_item('Configuración', None)
    elif route_name == 'ciclo_create':
        add_item('Configuración', reverse('matriculas:ciclo_list'))
        add_item('Registrar ciclo', None)
    elif route_name == 'turno_create':
        add_item('Configuración', reverse('matriculas:turno_list'))
        add_item('Registrar turno', None)
    elif route_name == 'horario_create':
        add_item('Configuración', reverse('matriculas:horario_list'))
        add_item('Registrar horario', None)

    elif route_name in {'lista_simulacros', 'crear_simulacro', 'gestionar_simulacro'}:
        add_item('Simulacros', None)
    elif route_name == 'crear_simulacro':
        add_item('Simulacros', reverse('matriculas:lista_simulacros'))
        add_item('Crear', None)

    elif route_name in {'lista_procedimientos', 'ver_procedimiento', 'crear_procedimiento', 'editar_procedimiento'}:
        add_item('Procedimientos', None)

    elif route_name in {'lista_usuarios', 'usuario_create', 'usuario_editar'}:
        add_item('Usuarios', None)

    elif route_name in {'reporte_financiero_anual', 'reporte_devengado'}:
        add_item('Reportes', None)

    elif route_name in {'resumen_general_pagos', 'cobranzas_vencidas'}:
        add_item('Pagos', None)

    elif route_name == 'editar_mensaje_whatsapp':
        add_item('Configuración', None)

    return {'breadcrumb': items}
