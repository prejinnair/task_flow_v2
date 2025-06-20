from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Task, Comment, Label, TestCase
from .forms import TaskForm, CommentForm, LabelForm, TestCaseForm
from projects.models import Project
from accounts.models import User
from django.db.models import Q
from accounts.decorators import permission_required
from django.http import JsonResponse
from django.utils.dateparse import parse_date

@login_required
def task_list(request):
    user = request.user

    if user.role in [0, 1]:  # Super Admin / Admin
        tasks = Task.objects.all().order_by('id')
        involved_projects = Project.objects.all()
        involved_users = User.objects.all()

    elif user.role == 2:  # Manager
        # Get users who report to this manager
        direct_reports = User.objects.filter(reporting_manager=user)

        # Get their tasks and tasks related to manager’s projects/teams
        user_teams = user.teams.all()
        involved_projects = Project.objects.filter(Q(teams__in=user_teams) | Q(managed_by=user)).distinct()

        tasks = Task.objects.filter(
            Q(project__in=involved_projects) |
            Q(assigned_to__in=direct_reports) |
            Q(created_by__in=direct_reports)
        ).distinct().order_by('id')

        involved_users = User.objects.filter(
            Q(teams__projects__in=involved_projects) |
            Q(id__in=direct_reports)
        ).distinct()

    else:
        # Regular User
        user_teams = user.teams.all()
        involved_projects = Project.objects.filter(Q(teams__in=user_teams) | Q(managed_by=user)).distinct()
        tasks = Task.objects.filter(project__in=involved_projects).order_by('id')
        involved_users = User.objects.filter(teams__projects__in=involved_projects).distinct()

    # Apply filters
    search = request.GET.get("search", "")
    project = request.GET.get("project")
    assigned_to = request.GET.get("assigned_to")
    priority = request.GET.get("priority")
    status = request.GET.get("status")
    type = request.GET.get("type")

    if search:
        tasks = tasks.filter(title__icontains=search)
    if project:
        tasks = tasks.filter(project_id=project)
    if assigned_to:
        tasks = tasks.filter(assigned_to_id=assigned_to)
    if priority:
        tasks = tasks.filter(priority=priority)
    if status:
        tasks = tasks.filter(status=status)
    if type:
        tasks = tasks.filter(type=type)

    context = {
        "tasks": tasks,
        "projects": involved_projects,
        "users": involved_users,
        "status_choices": Task.STATUS_CHOICES,
        "priority_choices": Task.PRIORITY_CHOICES,
        "type_choices": Task.TYPE_CHOICES,
    }
    return render(request, "tasks/task_list.html", context)



@login_required
def task_detail(request, pk):
    task = get_object_or_404(Task, pk=pk)
    comments = Comment.objects.filter(task=task).select_related('author')
    test_cases = TestCase.objects.filter(task=task)
    return render(request, 'tasks/task_detail.html', {
        'task': task,
        'comments': comments,
        'test_cases': test_cases
    })

@login_required
def task_create(request):
    related_test_case_id = request.GET.get('related_test_case')
    related_task_id = request.GET.get('related_task')

    initial_data = {}

    if related_test_case_id:
        test_case = get_object_or_404(TestCase, id=related_test_case_id)
        initial_data['title'] = f"Test Case {test_case.title} Failed"
        initial_data['description'] = f"Issue reported for Test Case: {test_case.title}"
    if related_task_id:
        try:
            related_task = Task.objects.get(id=related_task_id)
            initial_data['project'] = related_task.project_id
            initial_data['type'] = 'bug'
            initial_data['parent'] = related_task_id
            initial_data['assigned_to'] = related_task.assigned_to_id
        except Task.DoesNotExist:
            pass

    if request.method == 'POST':
        form = TaskForm(request.POST, user=request.user)
        files = request.FILES.getlist('attachments')

        if form.is_valid():
            task = form.save(commit=False)
            task.created_by = request.user
            task.save()
            form.save_m2m()

            # Save uploaded attachments
            for file in files:
                task.attachments.create(file=file, uploaded_by=request.user)

            messages.success(request, 'Task created successfully.')
            return redirect('tasks:task_detail', pk=task.pk)

    else:
        form = TaskForm(initial=initial_data, user=request.user)

    return render(request, 'tasks/task_form.html', {
        'form': form,
        'related_test_case': test_case,
        'related_task': related_task_id
    })


@login_required
def task_update(request, pk):
    task = get_object_or_404(Task, pk=pk)
    if request.method == 'POST':
        form = TaskForm(request.POST, instance=task, user=request.user)
        files = request.FILES.getlist('attachments')
        if form.is_valid():
            form.save()
            for file in files:
                task.attachments.create(file=file, uploaded_by=request.user)
            messages.success(request, 'Task updated successfully.')
            return redirect('tasks:task_detail', pk=task.pk)
    else:
        form = TaskForm(instance=task, user=request.user)
    return render(request, 'tasks/task_form.html', {'form': form})

@login_required
def task_delete(request, pk):
    task = get_object_or_404(Task, pk=pk)
    if request.method == 'POST':
        # Check if the user has permission to delete the task
        if not (request.user == task.created_by or request.user.role in [0, 1, 2]):
            messages.error(request, "You don't have permission to delete this task.")
            return redirect('tasks:task_detail', pk=pk)
        task.delete()
        messages.success(request, 'Task deleted successfully.')
        return redirect('tasks:task_list')
    return render(request, 'tasks/task_confirm_delete.html', {'task': task})

@login_required
def add_comment(request, task_id):
    task = get_object_or_404(Task, pk=task_id)
    if request.method == 'POST':
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.task = task
            comment.author = request.user
            comment.save()
            messages.success(request, 'Comment added successfully.')
            return redirect('tasks:task_detail', pk=task_id)
    else:
        form = CommentForm()
    return render(request, 'tasks/comment_form.html', {'form': form, 'task': task})

@login_required
def edit_comment(request, pk):
    comment = get_object_or_404(Comment, pk=pk, author=request.user)
    if request.method == 'POST':
        form = CommentForm(request.POST, instance=comment)
        if form.is_valid():
            form.save()
            messages.success(request, 'Comment updated.')
            return redirect('tasks:task_detail', pk=comment.task.pk)
    else:
        form = CommentForm(instance=comment)
    return render(request, 'tasks/comment_form.html', {'form': form, 'task': comment.task})

@login_required
def delete_comment(request, pk):
    comment = get_object_or_404(Comment, pk=pk, author=request.user)
    task_id = comment.task.pk
    if request.method == 'POST':
        comment.delete()
        messages.success(request, 'Comment deleted.')
        return redirect('tasks:task_detail', pk=task_id)
    return render(request, 'tasks/comment_confirm_delete.html', {'comment': comment})

@login_required
def label_list(request):
    labels = Label.objects.all()
    return render(request, 'tasks/label_list.html', {'labels': labels})

@login_required
def label_create(request):
    if request.method == 'POST':
        form = LabelForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Label created successfully.')
            return redirect('tasks:label_list')
    else:
        form = LabelForm()
    return render(request, 'tasks/label_form.html', {'form': form})


@login_required
def test_case_list(request):
    test_cases = TestCase.objects.select_related('task').all()
    return render(request, 'testcases/test_case_list.html', {'test_cases': test_cases})

@login_required
def test_case_list_by_task(request, task_id):
    task = get_object_or_404(Task, pk=task_id)
    test_cases = TestCase.objects.filter(task=task).select_related('created_by')
    return render(request, 'testcases/test_case_list.html', {'test_cases': test_cases, 'task': task})

@login_required
def test_case_detail(request, pk):
    test_case = get_object_or_404(TestCase, pk=pk)
    return render(request, 'testcases/test_case_detail.html', {'test_case': test_case})

@login_required
def test_case_create(request, task_id):
    if request.method == 'POST':
        form = TestCaseForm(request.POST)
        if form.is_valid():
            test_case = form.save(commit=False)
            test_case.created_by = request.user
            test_case.save()
            messages.success(request, 'Test case created successfully.')
            return redirect('tasks:test_case_detail', pk=test_case.pk)
    else:
        initial_data = {'task': task_id} if task_id else {}
        form = TestCaseForm(initial=initial_data)
    return render(request, 'testcases/test_case_form.html', {'form': form, 'title': 'Create Test Case'})

@login_required
def test_case_update(request, pk):
    test_case = get_object_or_404(TestCase, pk=pk)
    if request.method == 'POST':
        form = TestCaseForm(request.POST, instance=test_case)
        if form.is_valid():
            form.save()
            messages.success(request, 'Test case updated successfully.')
            return redirect('tasks:test_case_detail', pk=test_case.pk)
    else:
        form = TestCaseForm(instance=test_case)
    return render(request, 'testcases/test_case_form.html', {'form': form, 'title': 'Update Test Case'})

@login_required
def test_case_delete(request, pk):
    test_case = get_object_or_404(TestCase, pk=pk)
    if request.method == 'POST':
        test_case.delete()
        messages.success(request, 'Test case deleted successfully.')
        return redirect('tasks:test_case_list')
    return render(request, 'testcases/test_case_confirm_delete.html', {'test_case': test_case})


def task_update_ajax(request):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Invalid request method.'})

    task_id = request.POST.get('task_id')
    try:
        task = Task.objects.get(id=task_id)
    except Task.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Task not found.'})

    # Permission check
    if not (request.user == task.assigned_to or request.user == task.created_by or request.user.role in [0, 1, 2] or request.user == task.testing_assigned_to):
        return JsonResponse({'success': False, 'message': "You don't have permission to update this task."})

    # Basic fields
    task.title = request.POST.get('title', task.title)
    task.priority = request.POST.get('priority', task.priority)
    task.status = request.POST.get('status', task.status)
    task.due_date = request.POST.get('due_date') or task.due_date
    task.assigned_to_id = request.POST.get('assigned_to') or None

    task.estimated_hours = request.POST.get('estimated_hours') or None
    task.actual_hours = request.POST.get('actual_hours') or None

    completed_at_str = request.POST.get('completed_at')
    task.completed_at = parse_date(completed_at_str) if completed_at_str else None
    task.updated_by = request.user

    task.reviewed_by_id = request.POST.get('reviewed_by') or None
    task.testing_assigned_to_id = request.POST.get('testing_assigned_to') or None
    task.github_pr_url = request.POST.get('github_pr_url')
    task.save()
    return JsonResponse({'success': True})

def update_testcase_status(request, testcase_id):
    case = get_object_or_404(TestCase, id=testcase_id)
    new_status = request.POST.get('status')

    if new_status in dict(TestCase.STATUS_CHOICES).keys():
        case.status = new_status
        case.save()
        messages.success(request, 'Test case Status updated successfully.')
    return redirect('tasks:task_detail', pk=case.task.pk)