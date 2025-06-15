from django.db.models.signals import post_save, pre_save, m2m_changed, post_delete
from django.dispatch import receiver
from projects.models import Project, ProjectTeam
from tasks.models import ActivityLog, Team
from accounts.models import User
from django.utils.timezone import now

# Cache previous state for comparison
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
            # Status Change
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
            
            # Deadline Change
            if old.deadline != instance.deadline:
                ActivityLog.objects.create(
                    user=instance.updated_by,
                    action=f"📅 Project '{instance.name}' deadline updated to {instance.deadline}",
                    related_project=instance
                )

            # Manager change
            if old.managed_by != instance.managed_by:
                ActivityLog.objects.create(
                    user=instance.updated_by,
                    action=f"👨‍💼 Project '{instance.name}' manager changed to {instance.managed_by}",
                    related_project=instance
                )

            # Archive toggle
            if old.is_archived != instance.is_archived:
                action = "📦 archived" if instance.is_archived else "♻️ unarchived"
                ActivityLog.objects.create(
                    user=instance.updated_by,
                    action=f"📁 Project '{instance.name}' was {action}",
                    related_project=instance
                )

# Log when a team is assigned or removed from a project
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
    elif action == 'post_remove':
        # You may want to fetch team names before they're removed
        for pk in pk_set:
            ActivityLog.objects.create(
                user=instance.updated_by,
                action=f"👤 Team removed from Project '{instance.name}'",
                related_project=instance
            )


# TEAM CREATED / UPDATED
@receiver(post_save, sender=Team)
def log_team_save(sender, instance, created, **kwargs):
    user = instance.created_by if created else None
    if created:
        ActivityLog.objects.create(
            user=user,
            action=f"👥 Team '{instance.name}' was created.",
            related_team=instance
        )
    else:
        ActivityLog.objects.create(
            user=user or instance.created_by,
            action=f"✏️ Team '{instance.name}' was updated.",
            related_team=instance
        )

# TEAM DELETED
@receiver(post_delete, sender=Team)
def log_team_delete(sender, instance, **kwargs):
    ActivityLog.objects.create(
        user=instance.created_by,
        action=f"🗑️ Team '{instance.name}' was deleted.",
        related_team=None  # Team is deleted
    )

# TEAM MEMBERS ADDED / REMOVED
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

    elif action == 'post_remove':
        for pk in pk_set:
            member = User.objects.filter(pk=pk).first()
            if member:
                ActivityLog.objects.create(
                    user=instance.created_by,
                    action=f"➖ User '{member.username or member.email}' was removed from Team '{instance.name}'.",
                    related_team=instance
                )
