from django.contrib import admin
from .models import *

@admin.register(Alumno)
class AlumnoAdmin(admin.ModelAdmin):
    list_display = ('codigo', 'nombres_completos', 'grado_estudios', 'dni', 'sexo', 'activo', 'fondo_social')
    search_fields = ('codigo', 'nombres_completos', 'dni', 'colegio_de_procedencia', 'carrera_tentativa')
    list_filter = ('grado_estudios', 'sexo', 'activo')
    readonly_fields = ('codigo', 'fecha_registro')
    ordering = ('codigo',)
    fieldsets = (
        ("Datos Generales", {
            'fields': ('codigo', 'nombres_completos', 'dni', 'sexo', 'sexo_data', 'grado_estudios', 'fecha_nacimiento', 'activo', 'fondo_social')
        }),
        ("Contacto", {
            'fields': ('celular_llamadas', 'numero_whatsapp')
        }),
        ("Procedencia y Carrera", {
            'fields': ('colegio_de_procedencia', 'carrera_tentativa')
        }),
        ("Fotos", {
            'fields': ('foto_previa', 'foto_frente', 'foto_corte')
        }),
        ("Fechas", {
            'fields': ('fecha_registro',)
        }),
    )
    actions = ['activar_alumnos', 'desactivar_alumnos']
    
    def activar_alumnos(self, request, queryset):
        queryset.update(activo=True)
    activar_alumnos.short_description = "Activar alumnos seleccionados"
    
    def desactivar_alumnos(self, request, queryset):
        queryset.update(activo=False)
    desactivar_alumnos.short_description = "Desactivar alumnos seleccionados"

@admin.register(Apoderado)
class ApoderadoAdmin(admin.ModelAdmin):
    list_display = ('codigo', 'nombre_completo', 'mostrar_alumnos', 'dni', 'celular', 'parentesco', 'activo')
    search_fields = ('codigo', 'nombre_completo', 'dni')
    list_filter = ('parentesco',)
    readonly_fields = ('codigo', 'fecha_registro')
    ordering = ('codigo',)

    def mostrar_alumnos(self, obj):
        return ", ".join([alumno.codigo for alumno in obj.alumnos.all()])
    
    mostrar_alumnos.short_description = "Alumnos"

@admin.register(Ciclo)
class CicloAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'fecha_inicio', 'fecha_fin', 'activo', 'mostrar_turnos')
    search_fields = ('nombre',)
    list_filter = ('activo', 'fecha_inicio', 'fecha_fin')
    ordering = ('-fecha_inicio', 'nombre')
    filter_horizontal = ('turnos',)  # Mejor interfaz para seleccionar turnos
    actions = ['finalizar_ciclos']
    
    def mostrar_turnos(self, obj):
        return ", ".join([turno.nombre for turno in obj.turnos.all()])
    mostrar_turnos.short_description = "Turnos"
    
    def finalizar_ciclos(self, request, queryset):
        for ciclo in queryset:
            ciclo.finalizar_ciclo()
        self.message_user(request, f"{queryset.count()} ciclos finalizados correctamente")
    finalizar_ciclos.short_description = "Finalizar ciclos seleccionados"

@admin.register(Turno)
class TurnoAdmin(admin.ModelAdmin):
    list_display = ('nombre',)
    search_fields = ('nombre',)
    ordering = ('nombre',)

@admin.register(Horario)
class HorarioAdmin(admin.ModelAdmin):
    list_display = ('id', 'nombre', 'resumen_horario')

    def resumen_horario(self, obj):
        resumen = f"{obj.get_dias_bloque1_display()} {obj.hora_inicio1.strftime('%H:%M')} - {obj.hora_fin1.strftime('%H:%M')}"
        if obj.hora_inicio2 and obj.hora_fin2 and obj.dias_bloque2:
            resumen += f" / {obj.get_dias_bloque2_display()} {obj.hora_inicio2.strftime('%H:%M')} - {obj.hora_fin2.strftime('%H:%M')}"
        return resumen
    resumen_horario.short_description = "Horario"

@admin.register(Matricula)
class MatriculaAdmin(admin.ModelAdmin):
    list_display = (
        'codigo', 'alumno', 'apoderado', 'ciclo', 'turno', 'modalidad', 
        'estado', 'monto', 'cuotas', 'fecha_matricula'
    )
    search_fields = ('codigo', 'alumno__nombres_completos', 'apoderado__nombre_completo')
    list_filter = ('estado', 'modalidad', 'ciclo', 'turno')
    readonly_fields = ('codigo', 'fecha_matricula')
    ordering = ('-fecha_matricula',)

    list_select_related = ('alumno', 'apoderado', 'ciclo', 'turno', 'horario')
    actions = ['marcar_como_finalizadas']
    
    def marcar_como_finalizadas(self, request, queryset):
        queryset.update(estado='finalizada')
        self.message_user(request, f"{queryset.count()} matrículas marcadas como finalizadas")
    marcar_como_finalizadas.short_description = "Marcar como finalizadas"
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'alumno', 'apoderado', 'ciclo', 'turno', 'horario'
        )

@admin.register(Pago)
class PagoAdmin(admin.ModelAdmin):
    list_display = ('matricula', 'numero_cuota', 'estado', 'monto_pagado', 'fecha_pago')
    list_filter = ('estado', 'tipo_pago')
    search_fields = ('matricula__codigo', 'matricula__alumno__nombres_completos')

@admin.register(MensajeWhatsAppConfig)
class MensajeWhatsAppConfigAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'activo')
    search_fields = ('nombre',)
    list_filter = ('activo',) 

@admin.register(Perfil)
class PerfilAdmin(admin.ModelAdmin):
    list_display = ('user', 'tipo')
    list_filter = ('tipo',)

class AsistenciaInline(admin.TabularInline):
    model = AsistenciaSimulacro
    extra = 0
    fields = ('alumno_nombre', 'es_fondo', 'pago')
    readonly_fields = ('alumno_nombre', 'es_fondo')
    can_delete = False

    def alumno_nombre(self, obj):
        return obj.matricula.alumno.nombres_completos
    alumno_nombre.short_description = "Alumno"

    def es_fondo(self, obj):
        return "SÍ" if obj.matricula.alumno.fondo_social else ""
    es_fondo.short_description = "Fondo Social"

@admin.register(Simulacro)
class SimulacroAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'fecha', 'costo', 'ver_ganancia', 'ver_fondo', 'ver_deuda')
    inlines = [AsistenciaInline]
    actions = ['cargar_alumnos']

    def cargar_alumnos(self, request, queryset):
        for simulacro in queryset:
            matriculas = Matricula.objects.filter(ciclo=simulacro.ciclo, estado='activa')
            count = 0
            for mat in matriculas:
                obj, created = AsistenciaSimulacro.objects.get_or_create(
                    simulacro=simulacro, 
                    matricula=mat
                )
                if created:
                    obj.save()
                    count += 1
            self.message_user(request, f"Se cargaron {count} alumnos en {simulacro.nombre}")
    cargar_alumnos.short_description = "⚡ Cargar lista de alumnos"

    # COLUMNAS DE DINERO
    def ver_ganancia(self, obj):
        return f"S/ {obj.ganancia}"
    ver_ganancia.short_description = "Caja (Sí)"

    def ver_fondo(self, obj):
        return f"S/ {obj.total_fondo}"
    ver_fondo.short_description = "Fondo"

    def ver_deuda(self, obj):
        return f"S/ {obj.deuda}"
    ver_deuda.short_description = "Deuda"

@admin.register(FCMDevice)
class FCMDeviceAdmin(admin.ModelAdmin):
    list_display = ('user', 'creado_en', 'token')
    search_fields = ('user__username',)

class VentaAlumnoInline(admin.TabularInline):
    model = VentaAlumno
    extra = 1
    # autocomplete_fields = ['alumno'] # Descomentar si tienes muchos alumnos y definiste search_fields en AlumnoAdmin
    fields = ('alumno', 'cantidad', 'pagado', 'entregado', 'observacion')

# --- CONFIGURACIÓN DE SEGUIMIENTO ---
@admin.register(Seguimiento)
class SeguimientoAdmin(admin.ModelAdmin):
    list_display = ('matricula', 'usuario', 'fecha_registro', 'get_texto_corto')
    list_filter = ('usuario', 'fecha_registro')
    search_fields = ('matricula__alumno__apellido_paterno', 'matricula__alumno__nombres', 'texto')
    readonly_fields = ('fecha_registro',)

    def get_texto_corto(self, obj):
        # Muestra una vista previa del texto en la lista para que no ocupe tanto espacio
        return obj.texto[:50] + "..." if len(obj.texto) > 50 else obj.texto
    get_texto_corto.short_description = 'Contenido'

# --- CONFIGURACIÓN DE VENTAS ---
@admin.register(Venta)
class VentaAdmin(admin.ModelAdmin):
    list_display = ('codigo', 'descripcion', 'precio_unitario', 'get_total_recaudado', 'activo', 'fecha')
    list_filter = ('activo', 'fecha')
    search_fields = ('codigo', 'descripcion')
    inlines = [VentaAlumnoInline]

    def get_total_recaudado(self, obj):
        # Muestra el total calculado en el modelo Venta
        return f"S/. {obj.total_recaudado}"
    get_total_recaudado.short_description = 'Total Recaudado'

@admin.register(VentaAlumno)
class VentaAlumnoAdmin(admin.ModelAdmin):
    list_display = ('alumno', 'venta', 'cantidad', 'pagado', 'entregado', 'get_total_linea')
    list_filter = ('pagado', 'entregado', 'venta')
    search_fields = ('alumno__apellido_paterno', 'alumno__nombres', 'venta__descripcion')

    def get_total_linea(self, obj):
        # Muestra el subtotal (cantidad * precio)
        return f"S/. {obj.total}"
    get_total_linea.short_description = 'Subtotal'

class PasoInline(admin.TabularInline):
    model = Paso
    extra = 1
    fields = ('orden', 'descripcion')

@admin.register(Procedimiento)
class ProcedimientoAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'creado_por', 'creado_en', 'activo')
    search_fields = ('titulo',)
    list_filter = ('activo', 'creado_en')
    inlines = [PasoInline]
