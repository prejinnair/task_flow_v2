from django.shortcuts import render, redirect, get_object_or_404
from .forms import UserForm, LoginForm, UserProfileForm
from .models import User, UserProfile, UserPermission
from django.contrib import messages, auth
from .utils import detect_user, send_verification_email
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.exceptions import PermissionDenied
from django.utils.http import urlsafe_base64_decode
from django.contrib.auth.tokens import default_token_generator
from django.template.defaultfilters import slugify
from projects.models import Project, Team
from tasks.models import Task, TestCase, ActivityLog
from django.db.models import Q
from django.utils import timezone
from django.utils.timezone import now
from datetime import timedelta
from django.db.models import Count
import json
from django.core.serializers.json import DjangoJSONEncoder
from .decorators import permission_required


# Restrict the normal user from accessing the manager dashboard
def check_role_manager(user):
    if user.role == 2:
        return True
    else:
        raise PermissionDenied

# Restrict the normal user from accessing the qa dashboard
def check_role_qa(user):
    if user.role == 4:
        return True
    else:
        raise PermissionDenied

# Restrict the normal user from accessing the developer dashboard
def check_role_developer(user):
    if user.role == 3:
        return True
    else:
        raise PermissionDenied


def login(request):
    if request.user.is_authenticated:
        messages.warning(request, 'You are already logged in.')
        return redirect('accounts:my-account')

    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            user = auth.authenticate(request, email=email, password=password)

            if user is not None:
                auth.login(request, user)

                remember_me = request.POST.get('remember_me')
                if not remember_me:
                    request.session.set_expiry(0)
                else:
                    request.session.set_expiry(60 * 60 * 24 * 30)

                messages.success(request, f'Successfully Logged In as {request.user.username}.')
                return redirect('accounts:my-account')
            else:
                messages.error(request, 'Invalid email or password')
        else:
            messages.error(request, 'Please correct the errors below.')

    else:
        form = LoginForm()

    return render(request, 'accounts/login.html', {'form': form})



def logout(request):
    auth.logout(request)
    messages.info(request, 'You are logged out now.')
    return redirect('accounts:login')

@login_required
def my_account(request):
    user = request.user
    redirect_url = detect_user(user)
    return redirect(redirect_url)

@login_required
@user_passes_test(check_role_manager)
def manager_dashboard(request):
    user = request.user
    now_ts = now()
    week_ago = now_ts - timedelta(days=7)

    # Projects managed by the manager
    managed_projects = Project.objects.filter(managed_by=user)

    # Teams associated with the manager's projects
    related_teams = Team.objects.filter(projects__in=managed_projects).distinct()

    # Tasks associated with those projects
    related_tasks = Task.objects.filter(project__in=managed_projects).distinct()

    # Activity logs
    activity_logs = ActivityLog.objects.filter(
        Q(related_project__in=managed_projects) |
        Q(related_team__in=related_teams) |
        Q(related_task__in=related_tasks)
    ).order_by('-created_at')[:6]

    # Aggregate task status counts
    status_agg = related_tasks.values('status').annotate(count=Count('id'))

    # Map status to readable names
    status_display_map = dict(Task.STATUS_CHOICES)
    status_data = {
        status_display_map.get(item['status'], item['status'].title()): item['count']
        for item in status_agg
    }

    context = {
        'user_count': related_teams.values('members').distinct().count(),
        'team_count': related_teams.count(),
        'task_count': related_tasks.count(),
        'project_count': managed_projects.count(),
        'tasks_completed': related_tasks.filter(status='done').count(),
        'recent_activities': activity_logs,
        'recent_tasks': related_tasks.order_by('-created_at')[:10],
        'task_status_labels': json.dumps(list(status_data.keys()), cls=DjangoJSONEncoder),
        'task_status_counts': json.dumps(list(status_data.values()), cls=DjangoJSONEncoder),
        'projects': managed_projects,
    }
    return render(request, 'accounts/manager_dashboard.html', context)


@login_required
@user_passes_test(check_role_qa)
def qa_dashboard(request):
    user = request.user

    qa_tasks = Task.objects.filter(Q(assigned_to=user)| Q(testing_assigned_to=user))
    qa_assigned_count = qa_tasks.count()

    bugs_assigned_count = Task.objects.filter(created_by=user, type='bug').count()

    failed_test_cases_count = TestCase.objects.filter(
        status='failed'
    ).count()
    pending_verifications_count = TestCase.objects.filter(status__in=['pending', 'in_progress']).count()

    total_task_count = Task.objects.filter(status='done').count()

    recent_qa_tasks = Task.objects.filter(
        Q(created_by=user) | Q(testing_assigned_to=user), type='bug'
    ).order_by('-updated_at')[:10]

    activity_logs = ActivityLog.objects.filter(
        user=user
    ).order_by('-created_at')[:5]

    context = {
        'qa_assigned_count': qa_assigned_count,
        'bugs_assigned_count': bugs_assigned_count,
        'failed_test_cases_count': failed_test_cases_count,
        'uat_passed_count': total_task_count,
        'recent_qa_tasks': recent_qa_tasks,
        'activity_logs': activity_logs,
        'projects': Project.objects.filter(teams__in=user.teams.all()).distinct(),
        'in_progress_count': qa_tasks.filter(status='testing').count(),
        'pending_verifications_count': pending_verifications_count,
    }

    return render(request, 'accounts/qa_dashboard.html', context)


@login_required
@user_passes_test(check_role_developer)
def developer_dashboard(request):
    user = request.user
    now = timezone.now()

    assigned_tasks = Task.objects.filter(assigned_to=user)

    upcoming_tasks = (
        assigned_tasks
        .filter(
            due_date__gte=now,
            due_date__lte=now + timedelta(days=7)
        )
        .exclude(status='done')
        .order_by('due_date')
    )

    context = {
        'assigned_count': assigned_tasks.count(),
        'completed_count': assigned_tasks.filter(status='done').count(),
        'in_progress_count': assigned_tasks.filter(status='in_progress').count(),
        'blocked_count': assigned_tasks.filter(status='blocked').count(),
        'recent_tasks': assigned_tasks.order_by('-updated_at')[:5],
        'upcoming_tasks': upcoming_tasks,
        'activity_logs': ActivityLog.objects.filter(user=user).order_by('-created_at')[:5],
        'projects': Project.objects.filter(teams__in=user.teams.all()).distinct(),
    }

    return render(request, 'accounts/developer_dashboard.html', context)

@login_required
def guest_dashboard(request):   
    return render(request, 'accounts/guest_dashboard.html')

def forgot_password(request):
    if request.user.is_authenticated:
        messages.warning(request, 'You are already logged in.')
        return redirect('accounts:my-account')
    if request.method == 'POST':
        email = request.POST['email']
        user = User.objects.filter(email=email).exists()
        if user:
            user = User.objects.get(email__exact=email)
            # Send a reset password link to the user's email
            send_verification_email(user, action='reset_password')
            messages.success(request, 'Password reset link sent to your email.')
            return redirect('accounts:login')
        else:
            messages.error(request, 'Account with this email does not exist.')
            return redirect('accounts:forgot_password')
    return render(request, 'accounts/forgot_password.html')

def reset_password_validate(request, uidb64, token):
    # Validate the user by decoding the token and user pk
    auth.logout(request)
    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = User._default_manager.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None
    if user is not None and default_token_generator.check_token(user, token):
        request.session['uid'] = uid
        messages.info(request, 'Please reset your password')
        return redirect('accounts:reset_password')
    else:
        messages.error(request, 'This link has been expired!')
        return redirect('accounts:login')

def reset_password(request):
    if request.user.is_authenticated:
        messages.warning(request, 'You are already logged in.')
        return redirect('accounts:my-account')
    if request.method == 'POST':
        password = request.POST['password']
        confirm_password = request.POST['confirm_password']
        if password == confirm_password:
            uid = request.session.get('uid')
            user = User.objects.get(pk=uid)
            user.set_password(password)
            user.is_active = True
            user.save()
            messages.success(request, 'Password reset successfully')
            return redirect('accounts:login')
        else:
            messages.error(request, 'Password does not match!')
            return redirect('accounts:reset_password')

    return render(request, 'accounts/reset_password.html', {'user': request.user})

@login_required
def profile_view(request):
    return render(request, 'accounts/profile.html', {'user': request.user})

@permission_required('manage_users')
def user_list_view(request):
    user = request.user
    users = User.objects.filter(reporting_manager=user).distinct()

    return render(request, 'accounts/user_list.html', {'users': users})

@permission_required('manage_users')
def user_detail_view(request, user_id):
    user_obj = get_object_or_404(User, id=user_id)
    teams = user_obj.teams.all()
    projects = Project.objects.filter(teams__in=teams).distinct()


    if request.method == 'POST':
        selected_permissions = request.POST.getlist('permissions')

        # Remove permissions not in selected
        UserPermission.objects.filter(user=user_obj).exclude(permission__in=selected_permissions).delete()

        # Add new permissions
        for perm in selected_permissions:
            UserPermission.objects.get_or_create(
                user=user_obj,
                permission=perm,
                defaults={'granted_by': request.user}
            )

        messages.success(request, f"Permissions updated for {user_obj.username}.")
        return redirect('accounts:user_detail', user_id=user_id)

    # For rendering - get current permission keys
    current_permissions = set(
        UserPermission.objects.filter(user=user_obj).values_list('permission', flat=True)
    )

    return render(request, 'accounts/user_detail.html', {
        'user_obj': user_obj,
        'teams': teams,
        'projects': projects,
        'permission_choices': UserPermission.PERMISSION_CHOICES,
        'current_permissions': current_permissions,
    })

@login_required
def update_profile(request):
    profile, created = UserProfile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            return redirect('accounts:profile')
    else:
        form = UserProfileForm(instance=profile)

    return render(request, 'accounts/update_profile.html', {'form': form})