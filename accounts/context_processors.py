from projects.models import Project
def get_projects(request):
    """
    Context processor to add projects to the context for all templates.
    This allows easy access to projects in templates without needing to pass them explicitly.
    """
    user = request.user
    if user.is_authenticated:
        if user.role in [0, 1, 2]:
            projects = Project.objects.filter(managed_by=user)
        else:
            projects = Project.objects.filter(teams__in=user.teams.all()).distinct()
    else:
        projects = Project.objects.none()

    return {'projects': projects}
