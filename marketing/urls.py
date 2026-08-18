from django.urls import path
from marketing import views

app_name = 'marketing'

urlpatterns = [
    path('', views.dashboard, name='marketing_dashboard'),

    # Eventos
    path('eventos/', views.eventos, name='marketing_eventos'),
    path('eventos/nuevo/', views.nuevo_evento, name='marketing_nuevo_evento'),
    path('eventos/<int:pk>/', views.evento, name='marketing_evento'),
    path('eventos/<int:pk>/editar/', views.editar_evento, name='marketing_editar_evento'),
    path('eventos/<int:pk>/eliminar/', views.eliminar_evento, name='marketing_eliminar_evento'),
    path('eventos/<int:pk>/fotos/', views.fotos_evento, name='marketing_fotos_evento'),
    path('eventos/<int:pk>/fotos/descargar-todas/', views.descargar_todas_fotos, name='marketing_descargar_todas_fotos'),
    
    # Fotos de Eventos
    path('fotos/<int:pk>/eliminar/', views.eliminar_foto_evento, name='marketing_eliminar_foto_evento'),   

    #Alcances
    path('alcance/crear/', views.crear_alcance, name='crear_alcance'),
    path('alcance/<int:pk>/editar/', views.editar_alcance, name='editar_alcance'),
    path('alcance/<int:pk>/eliminar/', views.eliminar_alcance, name='eliminar_alcance'),

    # Publicaciones
    path('publicaciones/', views.publicaciones, name='marketing_publicaciones'),
    path('publicaciones/nueva/', views.nueva_publicacion, name='marketing_nueva_publicacion'),
    path('publicaciones/<int:pk>/', views.publicacion, name='marketing_publicacion'),
    path('publicaciones/<int:pk>/editar/', views.editar_publicacion, name='marketing_editar_publicacion'),
    path('publicaciones/<int:pk>/eliminar/', views.eliminar_publicacion, name='marketing_eliminar_publicacion'),
    path('publicaciones/<int:pk>/descargar-todos/', views.descargar_todos_archivos_publicacion, name='marketing_descargar_todos_archivos_publicacion'),
    
    # Recursos
    path('recursos/', views.recursos, name='marketing_recursos'),
    path('recursos/nuevo/', views.nuevo_recurso, name='marketing_nuevo_recurso'),
    path('recursos/<int:pk>/eliminar/', views.eliminar_recurso, name='marketing_eliminar_recurso'),
    path('recursos/<int:pk>/descargar/', views.descargar_recurso, name='marketing_descargar_recurso'),

    # Galería de Alumnos
    path('galeria-alumnos/', views.galeria_alumnos, name='marketing_galeria_alumnos'),
]