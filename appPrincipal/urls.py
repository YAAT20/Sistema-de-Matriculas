import os
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.http import FileResponse

def firebase_messaging_sw(request):
    file_path = os.path.join(settings.BASE_DIR, 'matriculas', 'static', 'matriculas', 'js', 'firebase-messaging-sw.js')
    
    return FileResponse(open(file_path, 'rb'), content_type='application/javascript')

urlpatterns = [
    path('admin/', admin.site.urls),    
    path('matriculas/', include('matriculas.urls', namespace='matriculas')),
    path('marketing/', include('marketing.urls', namespace='marketing')),   
    path('firebase-messaging-sw.js', firebase_messaging_sw),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)