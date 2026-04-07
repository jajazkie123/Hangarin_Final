import os
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.utils import timezone
from .models import Task, SubTask, Note, Category, Priority
from .forms import TaskForm, SubTaskForm, NoteForm, CategoryForm, PriorityForm
import requests


@login_required
def dashboard(request):
    user_tasks = Task.objects.all() if request.user.is_superuser else Task.objects.filter(user=request.user)
    total_tasks = user_tasks.count()
    completed_tasks = user_tasks.filter(status='Completed').count()
    pending_tasks = user_tasks.filter(status='Pending').count()
    in_progress_tasks = user_tasks.filter(status='In Progress').count()
    current_year = timezone.now().year
    tasks_this_year = user_tasks.filter(created_at__year=current_year).count()
    recent_tasks = user_tasks.order_by('-created_at')[:5]
    overdue_tasks = user_tasks.filter(
        deadline__lt=timezone.now()
    ).exclude(status='Completed').count()

    # --- Weather ---
    weather_data = None
    city = request.GET.get('city', 'Puerto Princesa')
    api_key = os.getenv('OPENWEATHER_API_KEY')
    try:
        url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        weather_data = {
            'city': data['name'],
            'country': data['sys']['country'],
            'temp': data['main']['temp'],
            'feels_like': data['main']['feels_like'],
            'humidity': data['main']['humidity'],
            'description': data['weather'][0]['description'].title(),
            'icon': data['weather'][0]['icon'],
        }
    except Exception as e:
        weather_data = {'error': 'Could not fetch weather data.'}

    context = {
        'total_tasks': total_tasks,
        'completed_tasks': completed_tasks,
        'pending_tasks': pending_tasks,
        'in_progress_tasks': in_progress_tasks,
        'tasks_this_year': tasks_this_year,
        'recent_tasks': recent_tasks,
        'overdue_tasks': overdue_tasks,
        'weather': weather_data,
        'city': city,
        'active_page': 'dashboard',
    }
    return render(request, 'tasks/dashboard.html', context)


@login_required
def task_list(request):
    # In task_list view
    tasks = Task.objects.all() if request.user.is_superuser else Task.objects.filter(user=request.user)

    # Search
    query = request.GET.get('q', '')
    if query:
        tasks = tasks.filter(
            Q(title__icontains=query) |
            Q(description__icontains=query) |
            Q(category__name__icontains=query)
        )

    # Filter by status
    status_filter = request.GET.get('status', '')
    if status_filter:
        tasks = tasks.filter(status=status_filter)

    # Filter by category
    category_filter = request.GET.get('category', '')
    if category_filter:
        tasks = tasks.filter(category__id=category_filter)

    # Filter by priority
    priority_filter = request.GET.get('priority', '')
    if priority_filter:
        tasks = tasks.filter(priority__id=priority_filter)

    # Sorting
    sort_by = request.GET.get('sort', '-created_at')
    sort_map = {
        'title': 'title',
        '-title': '-title',
        'created_at': 'created_at',
        '-created_at': '-created_at',
        'deadline': 'deadline',
        '-deadline': '-deadline',
        'status': 'status',
        '-status': '-status',
    }
    tasks = tasks.order_by(sort_map.get(sort_by, '-created_at'))

    # Pagination
    paginator = Paginator(tasks, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    categories = Category.objects.all()
    priorities = Priority.objects.all()

    context = {
        'page_obj': page_obj,
        'query': query,
        'status_filter': status_filter,
        'category_filter': category_filter,
        'priority_filter': priority_filter,
        'sort_by': sort_by,
        'categories': categories,
        'priorities': priorities,
        'active_page': 'tasks',
    }
    return render(request, 'tasks/task_list.html', context)


@login_required
def task_detail(request, pk):
    task = get_object_or_404(Task, pk=pk, user=request.user)
    subtasks = task.subtasks.all()
    notes = task.notes.all().order_by('-created_at')

    subtask_form = SubTaskForm()
    note_form = NoteForm()

    if request.method == 'POST':
        if 'add_subtask' in request.POST:
            subtask_form = SubTaskForm(request.POST)
            if subtask_form.is_valid():
                subtask = subtask_form.save(commit=False)
                subtask.parent_task = task
                subtask.save()
                messages.success(request, 'Subtask added successfully.')
                return redirect('task_detail', pk=pk)
        elif 'add_note' in request.POST:
            note_form = NoteForm(request.POST)
            if note_form.is_valid():
                note = note_form.save(commit=False)
                note.task = task
                note.save()
                messages.success(request, 'Note added successfully.')
                return redirect('task_detail', pk=pk)

    context = {
        'task': task,
        'subtasks': subtasks,
        'notes': notes,
        'subtask_form': subtask_form,
        'note_form': note_form,
        'active_page': 'tasks',
    }
    return render(request, 'tasks/task_detail.html', context)


@login_required
def task_create(request):
    if request.method == 'POST':
        form = TaskForm(request.POST)
        if form.is_valid():
            task = form.save(commit=False)
            task.user = request.user
            task.save()
            messages.success(request, 'Task created successfully.')
            return redirect('task_list')
    else:
        form = TaskForm()
    return render(request, 'tasks/task_form.html', {'form': form, 'action': 'Create', 'active_page': 'tasks'})


@login_required
def task_edit(request, pk):
    task = get_object_or_404(Task, pk=pk, user=request.user)
    if request.method == 'POST':
        form = TaskForm(request.POST, instance=task)
        if form.is_valid():
            form.save()
            messages.success(request, 'Task updated successfully.')
            return redirect('task_detail', pk=pk)
    else:
        form = TaskForm(instance=task)
    return render(request, 'tasks/task_form.html', {'form': form, 'action': 'Edit', 'task': task, 'active_page': 'tasks'})


@login_required
def task_delete(request, pk):
    task = get_object_or_404(Task, pk=pk, user=request.user)
    if request.method == 'POST':
        task.delete()
        messages.success(request, 'Task deleted successfully.')
        return redirect('task_list')
    return render(request, 'tasks/task_confirm_delete.html', {'task': task, 'active_page': 'tasks'})


@login_required
def subtask_delete(request, pk):
    subtask = get_object_or_404(SubTask, pk=pk, parent_task__user=request.user)
    task_pk = subtask.parent_task.pk
    if request.method == 'POST':
        subtask.delete()
        messages.success(request, 'Subtask deleted.')
    return redirect('task_detail', pk=task_pk)


@login_required
def subtask_toggle(request, pk):
    subtask = get_object_or_404(SubTask, pk=pk, parent_task__user=request.user)
    task_pk = subtask.parent_task.pk
    if subtask.status == 'Completed':
        subtask.status = 'Pending'
    else:
        subtask.status = 'Completed'
    subtask.save()
    return redirect('task_detail', pk=task_pk)


@login_required
def note_delete(request, pk):
    note = get_object_or_404(Note, pk=pk, task__user=request.user)
    task_pk = note.task.pk
    if request.method == 'POST':
        note.delete()
        messages.success(request, 'Note deleted.')
    return redirect('task_detail', pk=task_pk)


# --- Category Views ---
@login_required
def category_list(request):
    query = request.GET.get('q', '')
    categories = Category.objects.all()
    if query:
        categories = categories.filter(name__icontains=query)
    paginator = Paginator(categories, 10)
    page_obj = paginator.get_page(request.GET.get('page'))
    return render(request, 'tasks/category_list.html', {
        'page_obj': page_obj, 'query': query, 'active_page': 'categories'
    })


@login_required
def category_create(request):
    if request.method == 'POST':
        form = CategoryForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Category created.')
            return redirect('category_list')
    else:
        form = CategoryForm()
    return render(request, 'tasks/category_form.html', {'form': form, 'action': 'Create', 'active_page': 'categories'})


@login_required
def category_edit(request, pk):
    category = get_object_or_404(Category, pk=pk)
    if request.method == 'POST':
        form = CategoryForm(request.POST, instance=category)
        if form.is_valid():
            form.save()
            messages.success(request, 'Category updated.')
            return redirect('category_list')
    else:
        form = CategoryForm(instance=category)
    return render(request, 'tasks/category_form.html', {'form': form, 'action': 'Edit', 'active_page': 'categories'})


@login_required
def category_delete(request, pk):
    category = get_object_or_404(Category, pk=pk)
    if request.method == 'POST':
        category.delete()
        messages.success(request, 'Category deleted.')
        return redirect('category_list')
    return render(request, 'tasks/category_confirm_delete.html', {'category': category, 'active_page': 'categories'})


# --- Priority Views ---
@login_required
def priority_list(request):
    query = request.GET.get('q', '')
    priorities = Priority.objects.all()
    if query:
        priorities = priorities.filter(name__icontains=query)
    paginator = Paginator(priorities, 10)
    page_obj = paginator.get_page(request.GET.get('page'))
    return render(request, 'tasks/priority_list.html', {
        'page_obj': page_obj, 'query': query, 'active_page': 'priorities'
    })


@login_required
def priority_create(request):
    if request.method == 'POST':
        form = PriorityForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Priority created.')
            return redirect('priority_list')
    else:
        form = PriorityForm()
    return render(request, 'tasks/priority_form.html', {'form': form, 'action': 'Create', 'active_page': 'priorities'})


@login_required
def priority_edit(request, pk):
    priority = get_object_or_404(Priority, pk=pk)
    if request.method == 'POST':
        form = PriorityForm(request.POST, instance=priority)
        if form.is_valid():
            form.save()
            messages.success(request, 'Priority updated.')
            return redirect('priority_list')
    else:
        form = PriorityForm(instance=priority)
    return render(request, 'tasks/priority_form.html', {'form': form, 'action': 'Edit', 'active_page': 'priorities'})


@login_required
def priority_delete(request, pk):
    priority = get_object_or_404(Priority, pk=pk)
    if request.method == 'POST':
        priority.delete()
        messages.success(request, 'Priority deleted.')
        return redirect('priority_list')
    return render(request, 'tasks/priority_confirm_delete.html', {'priority': priority, 'active_page': 'priorities'})

@login_required
def subtask_list(request):
    subtasks = SubTask.objects.filter(parent_task__user=request.user)

    # Search
    query = request.GET.get('q', '')
    if query:
        subtasks = subtasks.filter(title__icontains=query)

    # Filter by status
    status_filter = request.GET.get('status', '')
    if status_filter:
        subtasks = subtasks.filter(status=status_filter)

    # Pagination
    paginator = Paginator(subtasks, 10)
    page_obj = paginator.get_page(request.GET.get('page'))

    return render(request, 'tasks/subtask_list.html', {
        'page_obj': page_obj,
        'query': query,
        'status_filter': status_filter,
        'active_page': 'subtasks',
    })


@login_required
def note_list(request):
    notes = Note.objects.filter(task__user=request.user).order_by('-created_at')

    # Search
    query = request.GET.get('q', '')
    if query:
        notes = notes.filter(content__icontains=query)

    # Sorting
    sort_by = request.GET.get('sort', '-created_at')
    if sort_by == 'oldest':
        notes = notes.order_by('created_at')
    else:
        notes = notes.order_by('-created_at')

    # Pagination
    paginator = Paginator(notes, 10)
    page_obj = paginator.get_page(request.GET.get('page'))

    return render(request, 'tasks/note_list.html', {
        'page_obj': page_obj,
        'query': query,
        'sort_by': sort_by,
        'active_page': 'notes',
    })