from django.contrib.auth.views import LogoutView
from django.urls import path

from .views import (
    HangarinLoginView, dashboard, home,
    TaskCreateView, TaskUpdateView,
    SubTaskCreateView, SubTaskUpdateView,
    CategoryCreateView, CategoryUpdateView,
    PriorityCreateView, PriorityUpdateView,
    NoteCreateView, NoteUpdateView
)

urlpatterns = [
    path("", home, name="home"),
    path("dashboard/", dashboard, name="dashboard"),
    
    path("tasks/add/", TaskCreateView.as_view(), name="task_add"),
    path("tasks/<int:pk>/edit/", TaskUpdateView.as_view(), name="task_edit"),
    
    path("subtasks/add/", SubTaskCreateView.as_view(), name="subtask_add"),
    path("subtasks/<int:pk>/edit/", SubTaskUpdateView.as_view(), name="subtask_edit"),
    
    path("categories/add/", CategoryCreateView.as_view(), name="category_add"),
    path("categories/<int:pk>/edit/", CategoryUpdateView.as_view(), name="category_edit"),
    
    path("priorities/add/", PriorityCreateView.as_view(), name="priority_add"),
    path("priorities/<int:pk>/edit/", PriorityUpdateView.as_view(), name="priority_edit"),
    
    path("notes/add/", NoteCreateView.as_view(), name="note_add"),
    path("notes/<int:pk>/edit/", NoteUpdateView.as_view(), name="note_edit"),

    path("login/", HangarinLoginView.as_view(), name="login"),
    path("logout/", LogoutView.as_view(), name="logout"),
]
