# forms.py

from django import forms
from .models import Task, Comment, Label, TestCase
from accounts.models import User
from projects.models import Project
from django.db.models import Q

class TailwindFormMixin:
    """Reusable mixin to apply Tailwind classes to all fields."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            if isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs.update({'class': 'form-checkbox rounded text-primary focus:ring-primary'})
            elif isinstance(field.widget, forms.RadioSelect):
                field.widget.attrs.update({'class': 'form-radio text-primary focus:ring-primary'})
            elif isinstance(field.widget, forms.CheckboxSelectMultiple):
                field.widget.attrs.update({'class': 'space-y-2'})
            elif isinstance(field.widget, forms.SelectMultiple):
                field.widget.attrs.update({'class': 'form-multiselect block w-full mt-1 border-gray-300 rounded-md shadow-sm focus:ring-primary focus:border-primary'})
            else:
                field.widget.attrs.update({'class': 'w-full mt-1 px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-primary focus:border-primary'})


class TaskForm(TailwindFormMixin, forms.ModelForm):
    class Meta:
        model = Task
        fields = [
            'title', 'description', 'type', 'project', 'assigned_to', 'status', 'priority', 'parent', 'start_date',
            'due_date', 'estimated_hours', 'actual_hours',  'completed_at',
        ]
        widgets = {
            'due_date': forms.DateInput(attrs={'type': 'date'}),
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'completed_at': forms.DateInput(attrs={'type': 'date'}),
            'description': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        # Filter projects based on user's teams
        if user:
            teams = user.teams.all()
            projects = Project.objects.filter(Q(teams__in=teams)| Q(managed_by=user), is_archived=False).distinct()
            self.fields['project'].queryset = projects
        else:
            self.fields['project'].queryset = Project.objects.none()

        # Limit assignable users based on allowed roles
        self.fields['assigned_to'].queryset = User.objects.filter(role__in=[3, 4, 5])



class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['text', 'is_internal']
        widgets = {
            'text': forms.Textarea(attrs={'rows': 4}),
        }

class LabelForm(TailwindFormMixin, forms.ModelForm):
    class Meta:
        model = Label
        fields = ['name', 'color']


class TestCaseForm(TailwindFormMixin, forms.ModelForm):
    class Meta:
        model = TestCase
        fields = ['title', 'description', 'expected_result', 'actual_result', 'status', 'task']
