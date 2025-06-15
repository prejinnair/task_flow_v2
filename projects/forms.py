from django import forms
from accounts.models import User
from .models import Team, Project, ProjectTeam


class TailwindFormMixin:
    """Reusable mixin to apply Tailwind CSS classes to all form fields."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            widget = field.widget
            if isinstance(widget, forms.CheckboxInput):
                widget.attrs.update({
                    'class': 'rounded text-blue-600 focus:ring-blue-500'
                })
            elif isinstance(widget, forms.CheckboxSelectMultiple):
                widget.attrs.update({
                    'class': 'space-y-2'
                })
            elif isinstance(widget, forms.SelectMultiple):
                widget.attrs.update({
                    'class': 'tom-select w-full mt-1 border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500'
                })

            elif isinstance(widget, forms.Select):
                widget.attrs.update({
                    'class': 'block w-full mt-1 border-gray-300 rounded-md shadow-sm bg-white focus:ring-blue-500 focus:border-blue-500'
                })
            elif isinstance(widget, forms.Textarea):
                widget.attrs.update({
                    'class': 'block w-full mt-1 resize-none border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500',
                    'rows': 3
                })
            elif isinstance(widget, forms.DateInput):
                widget.attrs.update({
                    'type': 'date',
                    'class': 'block w-full mt-1 border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500'
                })
            else:  # TextInput, NumberInput, etc.
                widget.attrs.update({
                    'class': 'block w-full mt-1 border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500'
                })


class TeamForm(TailwindFormMixin, forms.ModelForm):
    class Meta:
        model = Team
        fields = ['name', 'description', 'members', 'team_lead', 'status']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['members'].queryset = User.objects.filter(role__in=[3, 4, 5])  # team members


class ProjectForm(TailwindFormMixin, forms.ModelForm):
    class Meta:
        model = Project
        fields = [
            'name', 'description', 'teams', 'managed_by', 'start_date',
            'end_date', 'deadline', 'status', 'priority', 'is_archived'
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['managed_by'].queryset = User.objects.filter(role__in=[0, 1, 2])  # superadmin/admin/manager


class ProjectTeamForm(forms.ModelForm):
    class Meta:
        model = ProjectTeam
        fields = ['team', 'role', 'is_primary_team']

    def __init__(self, *args, **kwargs):
        project = kwargs.pop('project', None)  # get the passed project instance
        super().__init__(*args, **kwargs)
        if project:
            assigned_team_ids = project.teams.values_list('id', flat=True)
            self.fields['team'].queryset = Team.objects.exclude(id__in=assigned_team_ids)