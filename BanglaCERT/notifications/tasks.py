from .services import notify_incident_status_change


def send_incident_status_change_notification(incident, previous_status, new_status):
    return notify_incident_status_change(
        incident=incident,
        previous_status=previous_status,
        new_status=new_status,
    )
