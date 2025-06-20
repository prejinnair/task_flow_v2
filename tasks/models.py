from django.db import models
from accounts.models import User
from django.utils.text import slugify
from projects.models import Project, Team
from django.utils import timezone
from autoslug import AutoSlugField


class Task(models.Model):
    STATUS_CHOICES = [
        ('to_do', 'To Do'),
        ('in_progress', 'In Progress'),
        ('in_review', 'In Review'),
        ('testing', 'Testing'),
        ('done', 'Done'),
        ('blocked', 'Blocked'),
    ]

    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ]

    TYPE_CHOICES = [
        ('feature', 'Feature'),
        ('bug', 'Bug'),
        ('improvement', 'Improvement'),
        ('research', 'Research'),
        ('chore', 'Chore'),
    ]
    title = models.CharField(max_length=200)
    slug = AutoSlugField(populate_from='title', unique=True, always_update=False)
    task_key = models.CharField(max_length=50, unique=True, help_text="Unique identifier for the task", blank=True, null=True)
    description = models.TextField(blank=True)
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='tasks')
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_tasks')
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_tasks')
    reviewed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='reviewed_tasks')
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_tasks')
    testing_assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='tested_by')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='to_do')
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='medium')
    type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='feature')
    start_date = models.DateField(null=True, blank=True)
    due_date = models.DateField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='updated_tasks')
    labels = models.ManyToManyField('Label', blank=True, related_name='tasks')
    estimated_hours = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    actual_hours = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    is_blocking = models.BooleanField(default=False)
    blocked_by = models.ManyToManyField('self', blank=True, symmetrical=False, related_name='blocking')
    # sprint = models.ForeignKey('Sprint', on_delete=models.SET_NULL, null=True, blank=True, related_name='tasks')
    is_recurring = models.BooleanField(default=False)
    github_issue_url = models.URLField(blank=True, null=True)
    github_pr_url = models.URLField(blank=True, null=True)
    is_github_synced = models.BooleanField(default=False)
    parent = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='subtasks'
    )
    recurrence_interval = models.CharField(
        max_length=20,
        choices=[('daily', 'Daily'), ('weekly', 'Weekly'), ('monthly', 'Monthly')],
        blank=True,
        null=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.title)[:50]
            slug = base_slug
            counter = 1
            while Task.objects.filter(slug=slug).exists():
                slug = f"{base_slug[:45]}-{counter}"
                counter += 1
            self.slug = slug
        if not self.task_key:
            base_task_key = self.project.project_key.upper() if self.project.project_key else slugify(self.title)[:10]
            slug = f"{base_task_key}-1"
            counter = 1
            while Task.objects.filter(task_key=slug).exists():
                slug = f"{base_task_key[:45]}-{counter}"
                counter += 1
            self.task_key = slug
        super().save(*args, **kwargs)


    def __str__(self):
        return self.title

class Comment(models.Model):
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='comments')
    text = models.TextField()
    is_internal = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'Comment by {self.author} on {self.task}'

class Label(models.Model):
    name = models.CharField(max_length=50, unique=True)
    color = models.CharField(max_length=7, help_text="Hex color code like #ff6600")
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name


class TestCase(models.Model):
    STATUS_CHOICES = [
        ('not_tested', 'Not Tested'),
        ('passed', 'Passed'),
        ('failed', 'Failed'),
        ('blocked', 'Blocked'),
    ]

    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='test_cases')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    expected_result = models.TextField()
    actual_result = models.TextField(blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='test_cases')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='not_tested')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    def __str__(self):
        return f'Test Case: {self.title} for Task: {self.task.title}'

class TaskHistory(models.Model):
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='history')
    changed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='task_history')
    change_type = models.CharField(max_length=50)  # e.g., 'status_change', 'priority_change'
    old_value = models.TextField(blank=True)
    new_value = models.TextField(blank=True)
    change_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Change {self.change_type} for Task: {self.task.title} by {self.changed_by}'
    
class TaskAttachment(models.Model):
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='attachments')
    file = models.FileField(upload_to='task/attachments/')
    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='task_attachments')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Attachment for Task: {self.task.title} by {self.uploaded_by}'
    

class ActivityLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    action = models.TextField()
    created_at = models.DateTimeField(default=timezone.now)

    related_project = models.ForeignKey(Project, on_delete=models.SET_NULL, null=True, blank=True)
    related_team = models.ForeignKey(Team, on_delete=models.SET_NULL, null=True, blank=True)
    related_task = models.ForeignKey(Task, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"{self.user} - {self.action} at {self.created_at}"
