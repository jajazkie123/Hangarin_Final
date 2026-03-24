from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('tasks/', views.task_list, name='task_list'),
    path('tasks/create/', views.task_create, name='task_create'),
    path('tasks/<int:pk>/', views.task_detail, name='task_detail'),
    path('tasks/<int:pk>/edit/', views.task_edit, name='task_edit'),
    path('tasks/<int:pk>/delete/', views.task_delete, name='task_delete'),
    path('subtasks/<int:pk>/delete/', views.subtask_delete, name='subtask_delete'),
    path('subtasks/<int:pk>/toggle/', views.subtask_toggle, name='subtask_toggle'),
    path('notes/<int:pk>/delete/', views.note_delete, name='note_delete'),
    path('categories/', views.category_list, name='category_list'),
    path('categories/create/', views.category_create, name='category_create'),
    path('categories/<int:pk>/edit/', views.category_edit, name='category_edit'),
    path('categories/<int:pk>/delete/', views.category_delete, name='category_delete'),
    path('priorities/', views.priority_list, name='priority_list'),
    path('priorities/create/', views.priority_create, name='priority_create'),
    path('priorities/<int:pk>/edit/', views.priority_edit, name='priority_edit'),
    path('priorities/<int:pk>/delete/', views.priority_delete, name='priority_delete'),
    path('subtasks/', views.subtask_list, name='subtask_list'),
    path('notes/', views.note_list, name='note_list'),
]
