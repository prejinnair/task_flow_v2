from django.contrib import admin
from .models import Project, Team, ProjectTeam
from django import forms
from accounts.models import User

@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = ('name', 'team_lead', 'created_by', 'status', 'created_at')
    search_fields = ('name', 'description')
    filter_horizontal = ('members',)
    autocomplete_fields = ['team_lead', 'created_by']


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'status', 'priority', 'start_date', 'managed_by')
    list_filter = ('status', 'priority', 'managed_by')
    search_fields = ('name', 'description')
    autocomplete_fields = ['created_by']

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'managed_by':
            kwargs['queryset'] = User.objects.filter(role__in=[0, 1, 2])
        return super().formfield_for_foreignkey(db_field, request, **kwargs)
    

@admin.register(ProjectTeam)
class ProjectTeamAdmin(admin.ModelAdmin):
    list_display = ('project', 'team', 'role', 'is_primary_team', 'joined_at')
    list_filter = ('is_primary_team',)
    search_fields = ('role',)
    autocomplete_fields = ['project', 'team']
