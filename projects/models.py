from django.db import models
from accounts.models import User
from django.utils.text import slugify
from autoslug import AutoSlugField

class Team(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = AutoSlugField(populate_from='name', unique=True, always_update=False)
    description = models.TextField(blank=True)
    members = models.ManyToManyField(User, related_name='teams')
    team_lead = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='led_teams')
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_teams')
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='updated_teams')  # ADD THIS LINE
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    status = models.CharField(max_length=20, choices=[
        ('active', 'Active'),
        ('archived', 'Archived'),
    ], default='active')

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.name)[:50]
            slug = base_slug
            counter = 1
            while Team.objects.filter(slug=slug).exists():
                slug = f"{base_slug[:45]}-{counter}"  # ensure max length is not exceeded
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)


    def __str__(self):
        return self.name

    

class Project(models.Model):
    name = models.CharField(max_length=100)
    slug = AutoSlugField(populate_from='name', unique=True, always_update=False)
    project_key = models.CharField(max_length=50, unique=True, help_text="Unique identifier for the project", blank=True, null=True)
    description = models.TextField(blank=True)
    teams = models.ManyToManyField(Team, through='ProjectTeam', related_name='projects')
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_projects')
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    deadline = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=[
        ('not_started', 'Not Started'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('on_hold', 'On Hold'),
        ('cancelled', 'Cancelled'),
    ], default='not_started')
    priority = models.CharField(max_length=10, choices=[
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ], default='medium')
    is_archived = models.BooleanField(default=False)
    last_activity = models.DateTimeField(auto_now=True)
    managed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='managed_projects')
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='updated_projects')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.name)[:50]
            slug = base_slug
            counter = 1
            while Project.objects.filter(slug=slug).exists():
                slug = f"{base_slug[:45]}-{counter}"
                counter += 1
            self.slug = slug
        
        if not self.project_key:
            self.project_key = self.slug.upper()[:10]  # Generate project key from slug, ensuring it's unique and short
        super().save(*args, **kwargs)


    def __str__(self):
        return self.name


class ProjectTeam(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    team = models.ForeignKey(Team, on_delete=models.CASCADE)
    joined_at = models.DateTimeField(auto_now_add=True)
    role = models.CharField(max_length=50, blank=True, help_text="Team's role in the project")
    is_primary_team = models.BooleanField(default=False)

    class Meta:
        unique_together = ('project', 'team')

    def __str__(self):
        return f"{self.team.name} on {self.project.name}"
