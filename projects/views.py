from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from .models import Team, Project, ProjectTeam
from .forms import TeamForm, ProjectForm, ProjectTeamForm
from django.db.models import Q
from accounts.decorators import permission_required

# TEAM VIEWS
@login_required
def team_list(request):
    user = request.user
    if user.is_admin or user.is_superadmin:
        teams = Team.objects.all()
    else:
        member_teams = Team.objects.filter(members=user)
        managed_teams = Team.objects.filter(projects__managed_by=user)
        teams = (member_teams | managed_teams).distinct()
    return render(request, 'teams/team_list.html', {'teams': teams})

@login_required
def team_detail(request, pk):
    team = get_object_or_404(Team, pk=pk)
    return render(request, 'teams/team_detail.html', {'team': team})

@login_required
@permission_required('create_teams')
def team_create(request):
    if request.method == 'POST':
        form = TeamForm(request.POST)
        if form.is_valid():
            team = form.save(commit=False)
            team.created_by = request.user
            team.updated_by = request.user
            team.save()
            form.save_m2m()
            messages.success(request, 'Team created successfully.')
            return redirect('projects:team_list')
    else:
        form = TeamForm()
    return render(request, 'teams/team_form.html', {'form': form})

@login_required
@permission_required('manage_teams')
def team_update(request, pk):
    team = get_object_or_404(Team, pk=pk)
    if request.method == 'POST':
        form = TeamForm(request.POST, instance=team)
        if form.is_valid():
            team.updated_by = request.user
            form.save()
            messages.success(request, 'Team updated successfully.')
            return redirect('projects:team_list')
    else:
        form = TeamForm(instance=team)
    return render(request, 'teams/team_form.html', {'form': form})

@login_required
@permission_required('manage_teams')
def team_delete(request, pk):
    team = get_object_or_404(Team, pk=pk)
    if request.method == 'POST':
        team.delete()
        messages.success(request, 'Team deleted successfully.')
        return redirect('projects:team_list')
    return render(request, 'teams/team_confirm_delete.html', {'team': team})


# PROJECT VIEWS
@login_required
def project_list(request):
    user = request.user
    if user.is_admin or user.is_superadmin:
        projects = Project.objects.all()
    else:
        user_teams = user.teams.all()
        projects = Project.objects.filter(Q(teams__in=user_teams) | Q(managed_by=user)).distinct()
    return render(request, 'projects/project_list.html', {'projects': projects})


@login_required
def project_detail(request, pk):
    project = get_object_or_404(Project, pk=pk)
    teams = ProjectTeam.objects.filter(project=project)
    return render(request, 'projects/project_detail.html', {'project': project, 'teams': teams})

@login_required
@permission_required('create_project')
def project_create(request):
    if request.method == 'POST':
        form = ProjectForm(request.POST)
        if form.is_valid():
            project = form.save(commit=False)
            project.created_by = request.user
            project.save()
            form.save_m2m()
            messages.success(request, 'Project created successfully.')
            return redirect('projects:project_list')
    else:
        form = ProjectForm()
    return render(request, 'projects/project_form.html', {'form': form})

@login_required
@permission_required('manage_projects')
def project_update(request, pk):
    project = get_object_or_404(Project, pk=pk)
    if request.method == 'POST':
        form = ProjectForm(request.POST, instance=project)
        if form.is_valid():
            form.save()
            messages.success(request, 'Project updated successfully.')
            return redirect('projects:project_list', pk=project.pk)
    else:
        form = ProjectForm(instance=project)
    return render(request, 'projects/project_form.html', {'form': form})

@login_required
@permission_required('manage_projects')
def project_delete(request, pk):
    project = get_object_or_404(Project, pk=pk)
    if request.method == 'POST':
        project.delete()
        messages.success(request, 'Project deleted successfully.')
        return redirect('projects:project_list')
    return render(request, 'projects/project_confirm_delete.html', {'project': project})


# PROJECT TEAM ASSIGNMENT
@login_required
@permission_required('manage_projects')
def assign_team_to_project(request, pk):
    project = get_object_or_404(Project, id=pk)

    if request.method == 'POST':
        form = ProjectTeamForm(request.POST, project=project)
        if form.is_valid():
            team = form.cleaned_data['team']
            if ProjectTeam.objects.filter(project=project, team=team).exists():
                messages.warning(request, f"Team '{team.name}' is already assigned.")
                return redirect('projects:project_detail', pk=project.pk)

            project_team = form.save(commit=False)
            project_team.project = project
            project_team.save()

            messages.success(request, f"Team '{team.name}' assigned successfully.")
            return redirect('projects:project_detail', pk=project.pk)
    else:
        form = ProjectTeamForm(project=project)

    return render(request, 'projects/assign_team.html', {'form': form, 'project': project})


