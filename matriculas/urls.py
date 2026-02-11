
from django.urls import path
from matriculas.views import *

app_name = 'matriculas'  # Esto define el namespace

urlpatterns = [
    path('', dashboard_view, name='home'),
    
    path('dashboard/', dashboard_view, name='dashboard'),
    path('simulacros/crear/', crear_simulacro, name='crear_simulacro'),
    path('simulacros/', lista_simulacros, name='lista_simulacros'),
    path('simulacros/<int:simulacro_id>/gestionar/', gestionar_simulacro, name='gestionar_simulacro'),
    # Cobranza y recordatorios
    path('cobranzas/vencidas/', cobranza_vencidas_view, name='cobranzas_vencidas'),
    path('cobranzas/recordatorio/<int:apoderado_id>/', enviar_recordatorio_cobranza, name='enviar_recordatorio_cobranza'),

    # Configuración de WhatsApp
    path('config/mensaje-whatsapp/', editar_mensaje_whatsapp, name='editar_mensaje_whatsapp'),

    # Alumnos
    path('alumnos/', AlumnoListView.as_view(), name='alumno_list'),
    path('alumnos/historico/', AlumnoTotalListView.as_view(), name='alumno_total_list'),
    path('alumnos/exportar/excel/', exportar_alumnos_excel, name='exportar_alumnos_excel'),    
    path('alumnos/registrar/', AlumnoCreateView.as_view(), name='alumno_create'),
    path('alumnos/<int:pk>/', AlumnoDetailView.as_view(), name='alumno_detail'),
    path('alumnos/editar/<int:pk>/', AlumnoUpdateView.as_view(), name='alumno_update'),
    path('alumnos/eliminar/<int:pk>/', AlumnoDeleteView.as_view(), name='alumno_delete'),
    
    # Apoderados
    path('apoderados/', ApoderadoListView.as_view(), name='apoderado_list'),
    path('apoderados/registrar/',ApoderadoCreateView.as_view(), name='apoderado_create'),
    path('apoderados/registrar/<int:alumno_id>/', AsignarCrearApoderadoView.as_view(), name='asignar_apoderado'),
    path('apoderados/<int:pk>/', ApoderadoDetailView.as_view(), name='apoderado_detail'),
    path('apoderados/editar/<int:pk>/', ApoderadoUpdateView.as_view(), name='apoderado_update'),
    path('apoderados/eliminar/<int:pk>/', ApoderadoDeleteView.as_view(), name='apoderado_delete'),
    path('apoderado/asignar-existente/', asignar_apoderado_existente, name='asignar_apoderado_existente'),
    path('apoderados/exportar/', exportar_apoderados_alumnos_excel, name='exportar_apoderados_excel'),

    # Matrículas
    path('matriculas/', MatriculaListView.as_view(), name='matricula_list'),
    path('matriculas/registrar/', MatriculaCreateView.as_view(), name='matricula_create'),
    path('matriculas/registrar/<int:alumno_id>/', MatriculaCreateView.as_view(), name='matricula_create_alumno'),
    path('matriculas/<int:pk>/', MatriculaDetailView.as_view(), name='matricula_detail'),
    path('matriculas/<int:pk>/editar/', MatriculaUpdateView.as_view(), name='matricula_update'),
    path('matriculas/ficha/<uuid:pk>/pdf/', ficha_matricula_pdf, name='ficha_matricula_pdf'),
    path('matriculas/eliminar/<int:pk>/', MatriculaDeleteView.as_view(), name='matricula_delete'),
    path('matricula/<int:matricula_id>/enviar-ficha-whatsapp/', enviar_ficha_matricula_whatsapp, name='enviar_ficha_matricula_whatsapp'),
    path('matricula/<int:matricula_id>/enviar-ficha-whatsapp-estudiante/', enviar_ficha_matricula_whatsapp_estudiante, name='enviar_ficha_matricula_whatsapp_estudiante'),

    # Pagos
    path('pagos/matricula/<int:matricula_id>/', lista_pagos_matricula, name='lista_pagos_matricula'),
    path('pagos/matricula/<int:matricula_id>/registrar/', registrar_pago, name='registrar_pago'),
    path('pagos/editar/<int:pago_id>/', editar_pago, name='editar_pago'),
    path('pagos/resumen/', resumen_general_pagos, name='resumen_general_pagos'),
    path('ajax/confirmar-pago/<int:pago_id>/', confirmar_pago_ajax, name='ajax_confirmar_pago'),
    path('reporte-financiero/', reporte_financiero_anual, name='reporte_financiero_anual'),
    path('reporte-devengado/', reporte_financiero_devengado, name='reporte_devengado'),
    path('api/seguimiento/<int:matricula_id>/', api_seguimiento, name='api_seguimiento'),
    path('pagos/imprimir-deudas/', imprimir_reporte_deudas, name='imprimir_reporte_deudas'),
    path('cobranza/mensaje/<int:matricula_id>/<str:tipo_destinatario>/', enviar_mensaje_cobranza_general, name='enviar_mensaje_cobranza_general'),

    # AJAX
    path('ajax/apoderado-por-alumno/',   obtener_apoderado_por_alumno, name='ajax_apoderado_por_alumno'),
    path('ajax/alumnos-por-apoderado/', obtener_alumnos_por_apoderado, name='ajax_alumnos_por_apoderado'),
    path('ajax/todos-apoderados/', todos_apoderados, name='ajax_todos_apoderados'),
    path('ajax/todos-alumnos/', todos_alumnos, name='ajax_todos_alumnos'),
    path('ajax/buscar-alumnos/', buscar_alumnos, name='ajax_buscar_alumnos'),
    path('ajax/buscar-apoderados/', buscar_apoderados, name='ajax_buscar_apoderados'),

    # Configuración
    path('ciclos/', CicloListView.as_view(), name='ciclo_list'),
    path('ciclos/registrar/', CicloCreateView.as_view(), name='ciclo_create'),
    path('ciclos/editar/<int:pk>/', CicloUpdateView.as_view(), name='ciclo_update'),
    path('turnos/', TurnoListView.as_view(), name='turno_list'),
    path('turnos/registrar/', TurnoCreateView.as_view(), name='turno_create'),
    path('turnos/editar/<int:pk>/', TurnoUpdateView.as_view(), name='turno_update'),
    path('horarios/', HorarioListView.as_view(), name='horario_list'),
    path('horarios/registrar/', HorarioCreateView.as_view(), name='horario_create'),
    path('horarios/editar/<int:pk>/', HorarioUpdateView.as_view(), name='horario_update'),    
    path('horarios/eliminar/<int:pk>/', HorarioDeleteView.as_view(), name='horario_delete'),
    
    # Usuarios
    path('login/', CustomLoginView.as_view(), name='login'),
    path('logout/', CustomLogoutView.as_view(), name='logout'),
    path('password_change/', CustomPasswordChangeView.as_view(), name='password_change'),
    path('password_change/done/', CustomPasswordChangeDoneView.as_view(), name='password_change_done'),
    path('usuarios/crear/', UsuarioCreateView.as_view(), name='usuario_create'),
    path('usuario/editar/<int:pk>/', UsuarioUpdateView.as_view(), name='usuario_editar'),
    path('usuarios/', UsuarioListView.as_view(), name='lista_usuarios'),
]