import logging
from threading import Thread

from django.conf import settings
from django.core.mail import send_mail


logger = logging.getLogger(__name__)


def _status_label(incident, status_value):
    return dict(incident.STATUS_CHOICES).get(status_value, status_value)


def _build_status_change_email(incident, previous_status, new_status):
    new_status_label = _status_label(incident, new_status)
    previous_status_label = _status_label(incident, previous_status)
    subject = f"[BanglaCERT] Incident #{incident.id} status changed to {new_status_label}"
    message = (
        f"Your reported incident status has changed.\n\n"
        f"Incident ID: {incident.id}\n"
        f"Title: {incident.title}\n"
        f"Previous status: {previous_status_label}\n"
        f"New status: {new_status_label}\n\n"
        "Thank you,\n"
        "BanglaCERT Team"
    )
    return subject, message


def _build_submission_email(incident):
    subject = f"[BanglaCERT] Incident Report Received — #{incident.id}"
    
    tracking_section = ""
    if incident.public_tracking_id and incident.public_tracking_token:
        tracking_section = (
            f"\nYour anonymous tracking credentials:\n"
            f"  Tracking ID   : {incident.public_tracking_id}\n"
            f"  Access Token  : {incident.public_tracking_token}\n"
            f"\nKeep these safe — you will need them to check your report status.\n"
        )

    message = (
        f"Thank you for submitting your incident report to BanglaCERT.\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"  Report ID  : #{incident.id}\n"
        f"  Title      : {incident.title}\n"
        f"  Category   : {dict(incident.CATEGORY_CHOICES).get(incident.category, incident.category)}\n"
        f"  Status     : {dict(incident.STATUS_CHOICES).get(incident.status, incident.status)}\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"{tracking_section}\n"
        f"Our team will review your report and update you on any status changes.\n\n"
        f"Thank you,\n"
        f"BanglaCERT Incident Response Team"
    )
    return subject, message


def _get_notification_email(incident):
    if incident.reporter_email:
        return incident.reporter_email
    if incident.created_by and incident.created_by.email:
        return incident.created_by.email
    return ""


def _send_status_change_email(recipient_email, subject, message):
    send_mail(
        subject=subject,
        message=message,
        from_email=getattr(settings, "DEFAULT_FROM_EMAIL", "no-reply@banglacert.local"),
        recipient_list=[recipient_email],
        fail_silently=False,
    )


def _send_sync(incident, recipient_email, subject, message):
    try:
        _send_status_change_email(recipient_email, subject, message)
        return True, "sent"
    except Exception as exc:  # pragma: no cover
        logger.exception("Status change email failed for incident %s", incident.id)
        return False, str(exc)


def _send_async(incident, recipient_email, subject, message):
    def _target():
        try:
            _send_status_change_email(recipient_email, subject, message)
        except Exception:  # pragma: no cover
            logger.exception("Async status change email failed for %s", recipient_email)

    try: 
        Thread(target=_target, daemon=True).start()
        return True, "queued_async"
    except Exception as exc:  # pragma: no cover
        logger.exception("Could not queue async status email.")
        return False, str(exc)


def notify_incident_status_change_with_reason(incident, previous_status, new_status):
    if previous_status == new_status:
        return False, "Status was not changed."

    recipient_email = _get_notification_email(incident)
    if not recipient_email:
        return False, "No reporter email is available for this incident."

    subject, message = _build_status_change_email(incident, previous_status, new_status)

    if getattr(settings, "NOTIFICATION_EMAIL_ASYNC", False):
        sent, reason = _send_async(incident, recipient_email, subject, message)
        if sent:
            return True, reason
        return _send_sync(incident, recipient_email, subject, message)

    return _send_sync(incident, recipient_email, subject, message)


def notify_incident_status_change(incident, previous_status, new_status):
    sent, _ = notify_incident_status_change_with_reason(incident, previous_status, new_status)
    return sent


def notify_incident_submission(incident):
    recipient_email = _get_notification_email(incident)
    if not recipient_email:
        return False, "No reporter email is available for this incident."

    subject, message = _build_submission_email(incident)

    if getattr(settings, "NOTIFICATION_EMAIL_ASYNC", False):
        sent, reason = _send_async(incident, recipient_email, subject, message)
        if sent:
            return True, reason
        return _send_sync(incident, recipient_email, subject, message)

    return _send_sync(incident, recipient_email, subject, message)


def resend_incident_notification(incident, notification_type):
    """
    Force-resend a notification regardless of status change conditions.

    notification_type:
        'submission' — sends the submission confirmation again
        'status'     — resends the current status notification
    """
    recipient_email = _get_notification_email(incident)
    if not recipient_email:
        return False, "No reporter email is available for this incident."

    if notification_type == "submission":
        subject, message = _build_submission_email(incident)
    elif notification_type == "status":
        subject, message = _build_status_change_email(incident, incident.status, incident.status)
        # Override subject slightly for "reminder" context
        subject = f"[BanglaCERT] Incident #{incident.id} Status Update (Resend)"
    else:
        return False, f"Unknown notification type: {notification_type}"

    if getattr(settings, "NOTIFICATION_EMAIL_ASYNC", False):
        sent, reason = _send_async(incident, recipient_email, subject, message)
        if sent:
            return True, reason
        return _send_sync(incident, recipient_email, subject, message)

    return _send_sync(incident, recipient_email, subject, message)
