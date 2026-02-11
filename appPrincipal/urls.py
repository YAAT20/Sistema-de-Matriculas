from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views 
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView

urlpatterns = [
    # Redirección directa a tu app de matrículas
    path('', RedirectView.as_view(url='/matriculas/login/', permanent=False)),

    path('admin/', admin.site.urls),
    
    # Dejamos esto comentado porque usaremos el login de la app 'matriculas'
    # path('login/', ...),
    # path('logout/', ...),
    
    path('matriculas/', include('matriculas.urls', namespace='matriculas')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
