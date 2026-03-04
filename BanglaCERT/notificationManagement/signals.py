from django.db.models.signals import pre_save
from django.dispatch import receiver
from incidents.models import Incident
from django.core.mail import send_mail


@receiver(pre_save, sender=Incident)
def send_status_email(sender, instance, **kwargs):

    if not instance.pk:
        return

    old = Incident.objects.get(pk=instance.pk)

    if old.status != instance.status:

        if instance.created_by:

            send_mail(
                "Incident Status Updated",
                f"Status changed to {instance.status}",
                "noreply@banglacert.com",
                [instance.created_by.email],
                fail_silently=True,
            )