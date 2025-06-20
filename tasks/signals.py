from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from .models import Task, ActivityLog, Team
from projects.models import ProjectTeam
from notifications.models import Notification
from .utils import create_github_issue, send_teams_notification

@receiver(pre_save, sender=Task)
def cache_old_task_state(sender, instance, **kwargs):
    if instance.pk:
        try:
            instance._old_instance = Task.objects.get(pk=instance.pk)
        except Task.DoesNotExist:
            instance._old_instance = None


@receiver(post_save, sender=Task)
def log_task_update(sender, instance, created, **kwargs):
    team_obj = get_related_team(instance)

    # Create activity logs
    if created:
        ActivityLog.objects.create(
            user=instance.created_by,
            action=f"📝 Task '{instance.title}' created by {instance.created_by}",
            related_task=instance,
            related_project=instance.project,
            related_team=team_obj
        )
    elif instance.status == 'done' and instance.updated_by:
        ActivityLog.objects.create(
            user=instance.updated_by,
            action=f"✅ Task '{instance.title}' marked complete by {instance.updated_by}",
            related_task=instance,
            related_project=instance.project,
            related_team=team_obj
        )
    elif instance.updated_by:
        ActivityLog.objects.create(
            user=instance.updated_by,
            action=f"🔄 Task '{instance.title}' status updated to {instance.get_status_display()} by {instance.updated_by}",
            related_task=instance,
            related_project=instance.project,
            related_team=team_obj
        )

    # Get previous instance
    old = getattr(instance, '_old_instance', None)
    if (created and instance.assigned_to) or (old and old.assigned_to != instance.assigned_to and instance.assigned_to):
        Notification.objects.create(
            user=instance.assigned_to,
            message=f"You were assigned to task: {instance.title}",
            url=f"/tasks/{instance.id}/"
        )

    # Reviewer notification
    if old and old.reviewed_by != instance.reviewed_by and instance.reviewed_by:
        Notification.objects.create(
            user=instance.reviewed_by,
            message=f"You have been added as a reviewer to task: {instance.title}",
            url=f"/tasks/{instance.id}/"
        )

    # Status change notifications
    if (
        old and old.status != instance.status and instance.updated_by
    ):
        notifiable_users = set()

        # Add assigned_to, created_by, and testing_assigned_to (if available)
        if instance.assigned_to:
            notifiable_users.add(instance.assigned_to)
        if instance.created_by:
            notifiable_users.add(instance.created_by)
        if instance.testing_assigned_to:
            notifiable_users.add(instance.testing_assigned_to)

        # Remove the user who performed the update
        notifiable_users.discard(instance.updated_by)

        # Notify everyone else involved
        for user in notifiable_users:
            Notification.objects.create(
                user=user,
                message=f"Task '{instance.title}' status changed to {instance.get_status_display()} by {instance.updated_by}",
                url=f"/tasks/{instance.id}/"
            )
            message=f"Task '{instance.title}' status changed to {instance.get_status_display()} by {instance.updated_by}"
            send_teams_notification(message)


def get_related_team(task):
    related_team = ProjectTeam.objects.filter(project=task.project, is_primary_team=True).first()
    if related_team:
        return related_team.team
    if task.assigned_to:
        return task.assigned_to.teams.filter(projects=task.project).first()
    return None


# @receiver(post_save, sender=Task)
# def create_github_issue_on_assignment(sender, instance, created, **kwargs):
#     if created and instance.github_issue_url is None:
#         issue_title = f"[{instance.type.capitalize()}] {instance.title}"
#         issue_body = instance.description or f"Issue created for task: {instance.title}"
#         url = create_github_issue(issue_title, issue_body)
#         instance.github_issue_url = url
#         instance.save(update_fields=["github_issue_url"])
