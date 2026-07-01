import os
import firebase_admin
from firebase_admin import credentials, messaging
from django.conf import settings
from .models import FCMDevice
from django.contrib.auth.models import User
import threading

def inicializar_firebase():
    if not firebase_admin._apps:
        ruta_credenciales = os.path.join(settings.BASE_DIR, 'firebase-credenciales.json')
        cred = credentials.Certificate(ruta_credenciales)
        firebase_admin.initialize_app(cred)

def enviar_notificacion_push(usuario, titulo, cuerpo, url_destino="/matriculas/"):
    inicializar_firebase()
    
    dispositivos = FCMDevice.objects.filter(user=usuario)
    if not dispositivos.exists():
        return False, "Sin dispositivos."
        
    tokens = list(dispositivos.values_list('token', flat=True))
    
    mensaje = messaging.MulticastMessage(
        notification=messaging.Notification(
            title=titulo,
            body=cuerpo,
        ),
        data={
            "url": url_destino,
        },
        tokens=tokens,
    )
    
    try:
        respuesta = messaging.send_each_for_multicast(mensaje)
        return True, f"Enviado a {respuesta.success_count} dispositivos."
    except Exception as e:
        return False, str(e)
    
def notificar_admins(titulo, cuerpo, url_destino="/matriculas/", actor=None):
    inicializar_firebase() 

    admins = User.objects.filter(is_superuser=True)
    if actor:
        admins = admins.exclude(id=actor.id)

    tokens = list(FCMDevice.objects.filter(user__in=admins)
                                   .values_list('token', flat=True)
                                   .distinct())

    if not tokens:
        return False, "No hay administradores con dispositivos registrados."

    print(f"DEBUG: Enviando notificación a {len(tokens)} dispositivos únicos.")

    mensaje = messaging.MulticastMessage(
        data={
            "title": titulo,
            "body": cuerpo,
            "url": url_destino,
            "tag": "alerta-hooke"
        },
        tokens=tokens,
    )

    try:
        messaging.send_each_for_multicast(mensaje)
        return True, f"Notificación enviada a {len(tokens)} dispositivos admin."
    except Exception as e:
        return False, f"Error en envío masivo: {str(e)}"
    
def notificar_admins_async(titulo, cuerpo, url_destino="/matriculas/", actor=None):
    hilo = threading.Thread(
        target=notificar_admins,
        args=(titulo, cuerpo, url_destino, actor)
    )
    hilo.start()