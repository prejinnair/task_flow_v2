from django.db.models.signals import post_save, pre_save, m2m_changed, post_delete
from django.dispatch import receiver
from django.utils.timezone import now

from projects.models import Project, ProjectTeam
from tasks.models import ActivityLog, Team
from accounts.models import User
from notifications.models import Notification

# --- PROJECT SIGNALS ---

@receiver(pre_save, sender=Project)
def cache_old_project_state(sender, instance, **kwargs):
    if instance.pk:
        try:
            instance._old_instance = Project.objects.get(pk=instance.pk)
        except Project.DoesNotExist:
            instance._old_instance = None

@receiver(post_save, sender=Project)
def log_project_activity(sender, instance, created, **kwargs):
    old = getattr(instance, '_old_instance', None)

    if created:
        ActivityLog.objects.create(
            user=instance.created_by,
            action=f"📝 Project '{instance.name}' created",
            related_project=instance
        )
    else:
        if old:
            if old.status != instance.status:
                emoji = {
                    'not_started': '📝',
                    'in_progress': '🚧',
                    'completed': '✅',
                    'on_hold': '⏸️',
                    'cancelled': '❌'
                }.get(instance.status, '🔄')
                ActivityLog.objects.create(
                    user=instance.updated_by,
                    action=f"{emoji} Project '{instance.name}' status changed from '{old.status}' to '{instance.status}'",
                    related_project=instance
                )

            if old.deadline != instance.deadline:
                ActivityLog.objects.create(
                    user=instance.updated_by,
                    action=f"📅 Project '{instance.name}' deadline updated to {instance.deadline}",
                    related_project=instance
                )

            if old.managed_by != instance.managed_by:
                ActivityLog.objects.create(
                    user=instance.updated_by,
                    action=f"👨‍💼 Project '{instance.name}' manager changed to {instance.managed_by}",
                    related_project=instance
                )

            if old.is_archived != instance.is_archived:
                action = "📦 archived" if instance.is_archived else "♻️ unarchived"
                ActivityLog.objects.create(
                    user=instance.updated_by,
                    action=f"📁 Project '{instance.name}' was {action}",
                    related_project=instance
                )


@receiver(m2m_changed, sender=Project.teams.through)
def log_project_team_assignment(sender, instance, action, pk_set, **kwargs):
    if action == 'post_add':
        teams = ProjectTeam.objects.filter(project=instance, team__pk__in=pk_set)
        for pt in teams:
            ActivityLog.objects.create(
                user=instance.updated_by,
                action=f"👥 Team '{pt.team.name}' assigned to Project '{instance.name}'",
                related_project=instance
            )
            for member in pt.team.members.all():
                Notification.objects.create(
                    user=member,
                    message=f"📌 Your team '{pt.team.name}' was assigned to project '{instance.name}'",
                    url=f"/projects/{instance.id}/"
                )

    elif action == 'post_remove':
        teams = Team.objects.filter(pk__in=pk_set)
        for team in teams:
            ActivityLog.objects.create(
                user=instance.updated_by,
                action=f"👤 Team '{team.name}' removed from Project '{instance.name}'",
                related_project=instance
            )
            for member in team.members.all():
                Notification.objects.create(
                    user=member,
                    message=f"📌 Your team '{team.name}' was removed from project '{instance.name}'",
                    url=f"/projects/{instance.id}/"
                )


# --- TEAM SIGNALS ---

@receiver(post_save, sender=Team)
def log_team_save(sender, instance, created, **kwargs):
    user = instance.created_by if created else instance.updated_by or instance.created_by
    if created:
        ActivityLog.objects.create(
            user=user,
            action=f"👥 Team '{instance.name}' was created.",
            related_team=instance
        )
    else:
        ActivityLog.objects.create(
            user=user,
            action=f"✏️ Team '{instance.name}' was updated.",
            related_team=instance
        )

@receiver(post_delete, sender=Team)
def log_team_delete(sender, instance, **kwargs):
    ActivityLog.objects.create(
        user=instance.created_by,
        action=f"🗑️ Team '{instance.name}' was deleted.",
        related_team=None
    )


@receiver(m2m_changed, sender=Team.members.through)
def log_team_member_change(sender, instance, action, pk_set, **kwargs):
    if action == 'post_add':
        for pk in pk_set:
            member = User.objects.filter(pk=pk).first()
            if member:
                ActivityLog.objects.create(
                    user=instance.created_by,
                    action=f"➕ User '{member.username or member.email}' was added to Team '{instance.name}'.",
                    related_team=instance
                )
                Notification.objects.create(
                    user=member,
                    message=f"👥 You were added to Team '{instance.name}'",
                    url=f"/projects/teams/{instance.id}/"
                )

    elif action == 'post_remove':
        for pk in pk_set:
            member = User.objects.filter(pk=pk).first()
            if member:
                ActivityLog.objects.create(
                    user=instance.created_by,
                    action=f"➖ User '{member.username or member.email}' was removed from Team '{instance.name}'.",
                    related_team=instance
                )
                Notification.objects.create(
                    user=member,
                    message=f"👥 You were removed from Team '{instance.name}'",
                    url=f"/projects/teams/{instance.id}/"
                )
