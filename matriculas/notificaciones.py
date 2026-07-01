from django.contrib.auth.models import User
from fcm_django.models import FCMDevice
from .firebase import enviar_push

def notificar_admins(titulo, cuerpo, url_destino="/matriculas/", actor=None):
    admins = User.objects.filter(is_superuser=True)

    if actor:
        admins = admins.exclude(id=actor.id)

    tokens = list(
        FCMDevice.objects.filter(user__in=admins)
        .values_list("token", flat=True)
        .distinct()
    )   

    data = {
        "tipo": "admin_alerta",
        "url": url_destino,
    }

    return enviar_push(tokens, titulo, cuerpo, data)

def notificar_pago_matricula(pago):
    matricula = pago.matricula
    alumno = getattr(matricula, "alumno", None)

    titulo = "Pago registrado"
    cuerpo = f"Se registró un pago de S/ {pago.monto}"

    data = {
        "tipo": "pago_matricula",
        "matricula_id": str(matricula.id),
        "alumno": str(alumno) if alumno else "",
        "monto": str(pago.monto),
        "url": f"/matriculas/{matricula.id}/pagos/",
    }

    admins = User.objects.filter(is_superuser=True)

    tokens = list(
        FCMDevice.objects.filter(user__in=admins)
        .values_list("token", flat=True)
        .distinct()
    )

    return enviar_push(tokens, titulo, cuerpo, data)