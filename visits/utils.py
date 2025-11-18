# visits/utils.py
import threading
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings


def send_visit_completed_email_async(visit):
    """
    Envía un correo al cliente cuando la visita se completa,
    pero lo hace en un hilo aparte para no trabar la respuesta HTTP.
    """
    def _send():
        # intentar sacar el correo del cliente desde la suscripción
        sub = getattr(visit, "subscription", None)
        customer = getattr(sub, "customer", None) if sub else None
        to_email = getattr(customer, "email", None)

        if not to_email:
            # si no hay correo no mandamos nada
            return

        subject = f"Visita #{visit.id} completada"

        # armamos el contexto con lo que pediste
        materials = visit.materials_used.all()
        tasks = visit.tasks_completed.filter(completada=True)
        evidences = visit.evidences.all()

        context = {
            "visit": visit,
            "customer": customer,
            "materials": materials,
            "tasks": tasks,
            "evidences": evidences,
        }

        # estos templates los creamos más abajo
        text_body = render_to_string("emails/visit_completed.txt", context)
        html_body = render_to_string("emails/visit_completed.html", context)

        send_mail(
            subject,
            text_body,
            getattr(settings, "DEFAULT_FROM_EMAIL", None),
            [to_email],
            html_message=html_body,
            fail_silently=True,  # para que no rompa la vista si hay error de smtp
        )

    threading.Thread(target=_send, daemon=True).start()
