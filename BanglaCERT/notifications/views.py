from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from .models import Notification

@login_required
def get_notifications(request):
    """
    Returns unread count and the 10 most recent notifications for the logged-in user.
    """
    unread_count = Notification.objects.filter(recipient=request.user, is_read=False).count()
    recent_notifications = Notification.objects.filter(recipient=request.user).order_by('-created_at')[:10]
    
    notifications_data = []
    for n in recent_notifications:
        notifications_data.append({
            'id': n.id,
            'message': n.message,
            'url': n.url,
            'is_read': n.is_read,
            'created_at': n.created_at.strftime("%Y-%m-%d %H:%M:%S"),
        })
        
    return JsonResponse({
        'unread_count': unread_count,
        'notifications': notifications_data
    })

@login_required
def mark_all_read(request):
    """
    Marks all notifications for the current user as read.
    """
    if request.method == 'POST':
        Notification.objects.filter(recipient=request.user, is_read=False).update(is_read=True)
        return JsonResponse({'status': 'ok'})
    return JsonResponse({'status': 'error', 'message': 'Only POST allowed'}, status=405)
