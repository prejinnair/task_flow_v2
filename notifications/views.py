# notifications/views.py

from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from .models import Notification

@login_required
def notification_list(request):
    user = request.user
    unread_notifications = user.notifications.filter(is_read=False).order_by('-created_at')
    read_notifications = user.notifications.filter(is_read=True).order_by('-created_at')
    
    return render(request, 'notifications/list.html', {
        'unread_notifications': unread_notifications,
        'read_notifications': read_notifications,
    })


@login_required
def mark_as_read(request, pk):
    note = get_object_or_404(Notification, pk=pk, user=request.user)
    note.is_read = True
    note.save()
    return redirect(note.url or 'notifications:list')
