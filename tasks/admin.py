from django.contrib import admin
from .models import Task, Comment, Label, TestCase

@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ('title', 'project', 'assigned_to', 'status', 'priority', 'due_date', 'created_at')
    list_filter = ('status', 'priority', 'due_date', 'project')
    search_fields = ('title', 'description')
    autocomplete_fields = ['project', 'assigned_to']
    ordering = ['-created_at']

@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('task', 'author', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('text',)
    autocomplete_fields = ['task', 'author']

@admin.register(Label)
class LabelAdmin(admin.ModelAdmin):
    list_display = ('name', 'color')
    search_fields = ('name',)

@admin.register(TestCase)
class TestCaseAdmin(admin.ModelAdmin):
    list_display = ('title', 'task', 'created_by', 'status', 'created_at')
    list_filter = ('status',)
    search_fields = ('title', 'description', 'expected_result', 'actual_result')
    autocomplete_fields = ['task', 'created_by']
