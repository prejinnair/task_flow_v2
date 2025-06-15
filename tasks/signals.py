from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Task, ActivityLog

@receiver(post_save, sender=Task)
def log_task_update(sender, instance, created, **kwargs):
    if created:
        ActivityLog.objects.create(
            user=instance.created_by,
            action=f"📝 Task '{instance.title}' created by {instance.created_by}",
            related_task=instance,
            related_project=instance.project
        )
    elif instance.status == 'done' and instance.updated_by:
        ActivityLog.objects.create(
            user=instance.updated_by,
            action=f"✅ Task '{instance.title}' marked complete by {instance.updated_by}",
            related_task=instance,
            related_project=instance.project
        )
    elif instance.updated_by:
        ActivityLog.objects.create(
            user=instance.updated_by,
                action=f"🔄 Task '{instance.title}' updated by {instance.updated_by}",
                related_task=instance,
            related_project=instance.project
        )
