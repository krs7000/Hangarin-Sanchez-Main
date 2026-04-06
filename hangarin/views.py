from datetime import datetime, time, timedelta
from urllib.parse import urlencode

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView
from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.shortcuts import redirect, render
from django.urls import reverse, reverse_lazy
from django.views.generic import CreateView, UpdateView

from .forms import (
    HangarinAuthenticationForm,
    CategoryForm,
    NoteForm,
    PriorityForm,
    SubTaskForm,
    TaskForm,
)
from .models import Category, Note, Priority, StatusChoices, SubTask, Task

MAIN_TABS = {"dashboard", "tasks", "subtasks", "categories", "priorities", "notes"}
OPEN_STATUSES = [StatusChoices.PENDING, StatusChoices.IN_PROGRESS]

STATUS_BADGE_CLASSES = {
    StatusChoices.PENDING: "status-pill status-pill-pending",
    StatusChoices.IN_PROGRESS: "status-pill status-pill-progress",
    StatusChoices.COMPLETED: "status-pill status-pill-complete",
}
STATUS_BAR_CLASSES = {
    StatusChoices.PENDING: "meter-bar meter-bar-pending",
    StatusChoices.IN_PROGRESS: "meter-bar meter-bar-progress",
    StatusChoices.COMPLETED: "meter-bar meter-bar-complete",
}
PRIORITY_BADGE_CLASSES = {
    "critical": "priority-pill priority-pill-critical",
    "high": "priority-pill priority-pill-high",
    "medium": "priority-pill priority-pill-medium",
    "low": "priority-pill priority-pill-low",
    "optional": "priority-pill priority-pill-optional",
}


class HangarinLoginView(LoginView):
    authentication_form = HangarinAuthenticationForm
    redirect_authenticated_user = True
    template_name = "registration/login.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["social_login_enabled"] = settings.SOCIAL_LOGIN_ENABLED
        return context


def home(request):
    if request.user.is_authenticated:
        return redirect("dashboard")
    return redirect("login")


@login_required
def dashboard(request):
    now = timezone.localtime()
    today = timezone.localdate()
    start_of_today = timezone.make_aware(datetime.combine(today, time.min))
    start_of_tomorrow = start_of_today + timedelta(days=1)
    week_horizon = start_of_today + timedelta(days=7)

    active_tab = request.GET.get("tab", "dashboard").strip().lower()
    query = request.GET.get("q", "").strip()
    selected_status = request.GET.get("status", "").strip()
    page_number = request.GET.get("page")

    if active_tab not in MAIN_TABS:
        active_tab = "dashboard"
    if selected_status not in StatusChoices.values:
        selected_status = ""

    dashboard_url = reverse("dashboard")

    main_nav = [
        {
            "label": "Dashboard",
            "url": _build_url(dashboard_url, tab="dashboard"),
            "active": active_tab == "dashboard",
        },
        {
            "label": "Tasks",
            "url": _build_url(dashboard_url, tab="tasks"),
            "active": active_tab == "tasks",
        },
        {
            "label": "Sub Tasks",
            "url": _build_url(dashboard_url, tab="subtasks"),
            "active": active_tab == "subtasks",
        },
        {
            "label": "Categories",
            "url": _build_url(dashboard_url, tab="categories"),
            "active": active_tab == "categories",
        },
        {
            "label": "Priorities",
            "url": _build_url(dashboard_url, tab="priorities"),
            "active": active_tab == "priorities",
        },
        {
            "label": "Notes",
            "url": _build_url(dashboard_url, tab="notes"),
            "active": active_tab == "notes",
        },
    ]

    task_status_totals = {
        row["status"]: row["count"]
        for row in Task.objects.values("status").annotate(count=Count("id"))
    }
    subtask_status_totals = {
        row["status"]: row["count"]
        for row in SubTask.objects.values("status").annotate(count=Count("id"))
    }

    total_tasks = Task.objects.count()
    pending_tasks = task_status_totals.get(StatusChoices.PENDING, 0)
    in_progress_tasks = task_status_totals.get(StatusChoices.IN_PROGRESS, 0)
    completed_tasks = task_status_totals.get(StatusChoices.COMPLETED, 0)
    open_tasks = pending_tasks + in_progress_tasks

    total_subtasks = SubTask.objects.count()
    pending_subtasks = subtask_status_totals.get(StatusChoices.PENDING, 0)
    in_progress_subtasks = subtask_status_totals.get(StatusChoices.IN_PROGRESS, 0)
    completed_subtasks = subtask_status_totals.get(StatusChoices.COMPLETED, 0)

    total_categories = Category.objects.count()
    total_priorities = Priority.objects.count()
    notes_count = Note.objects.count()
    tasks_with_notes_count = Task.objects.filter(notes__isnull=False).distinct().count()

    due_today_count = Task.objects.filter(
        deadline__gte=start_of_today,
        deadline__lt=start_of_tomorrow,
        status__in=OPEN_STATUSES,
    ).count()
    week_due_count = Task.objects.filter(
        deadline__gte=start_of_today,
        deadline__lt=week_horizon,
        status__in=OPEN_STATUSES,
    ).count()
    overdue_tasks_count = Task.objects.filter(
        deadline__lt=now,
        status__in=OPEN_STATUSES,
    ).count()
    recent_notes_count = Note.objects.filter(
        created_at__gte=timezone.now() - timedelta(days=7)
    ).count()

    completion_rate = round((completed_tasks / total_tasks) * 100) if total_tasks else 0

    task_base_queryset = Task.objects.select_related("category", "priority").annotate(
        note_count=Count("notes", distinct=True),
        total_subtasks=Count("subtasks", distinct=True),
        completed_subtask_count=Count(
            "subtasks",
            filter=Q(subtasks__status=StatusChoices.COMPLETED),
            distinct=True,
        ),
    )

    recent_task_updates = [
        _decorate_task(task, now)
        for task in task_base_queryset.order_by("-updated_at", "deadline", "title")[:6]
    ]
    for task in recent_task_updates:
        task.notes_url = _build_url(dashboard_url, tab="notes", q=task.title)

    upcoming_deadlines = [
        _decorate_task(task, now)
        for task in task_base_queryset.filter(status__in=OPEN_STATUSES).order_by(
            "deadline",
            "title",
        )[:5]
    ]
    for task in upcoming_deadlines:
        task.edit_url = reverse("task_edit", args=[task.pk])

    dashboard_categories = list(
        Category.objects.annotate(
            task_count=Count("tasks", distinct=True),
            completed_count=Count(
                "tasks",
                filter=Q(tasks__status=StatusChoices.COMPLETED),
                distinct=True,
            ),
        ).order_by("-task_count", "name")[:5]
    )
    for category in dashboard_categories:
        category.share_percent = (
            round((category.task_count / total_tasks) * 100) if total_tasks else 0
        )

    dashboard_recent_notes = list(
        Note.objects.select_related("task", "task__category", "task__priority")
        .order_by("-updated_at")[:5]
    )
    for note in dashboard_recent_notes:
        note.edit_url = reverse("note_edit", args=[note.pk])

    dashboard_stats = [
        {"label": "Total Tasks", "value": total_tasks, "tone": "neutral"},
        {"label": "Pending", "value": pending_tasks, "tone": "warning"},
        {"label": "In Progress", "value": in_progress_tasks, "tone": "info"},
        {"label": "Completed", "value": completed_tasks, "tone": "success"},
    ]
    dashboard_summary_cards = [
        {"label": "Subtasks", "value": total_subtasks},
        {"label": "Notes", "value": notes_count},
        {"label": "Categories", "value": total_categories},
        {"label": "Priorities", "value": total_priorities},
    ]
    status_flow = []
    for status in StatusChoices:
        count = task_status_totals.get(status.value, 0)
        status_flow.append(
            {
                "label": status.label,
                "count": count,
                "percent": round((count / total_tasks) * 100) if total_tasks else 0,
                "bar_class": STATUS_BAR_CLASSES.get(status.value, "meter-bar"),
            }
        )

    panel_title = "Dashboard"
    panel_eyebrow = "Workspace Overview"
    panel_copy = "Monitor delivery pace, note activity, and deadline pressure from one control surface."
    panel_action_label = "Open Task Workspace"
    panel_action_url = _build_url(dashboard_url, tab="tasks")
    table_rows = []
    panel_stats = []
    status_filters = []
    search_placeholder = ""
    table_count = 0
    pagination = None

    if active_tab == "tasks":
        task_search_queryset = task_base_queryset.order_by("deadline", "title")
        if query:
            task_search_queryset = task_search_queryset.filter(
                Q(title__icontains=query)
                | Q(description__icontains=query)
                | Q(category__name__icontains=query)
                | Q(priority__name__icontains=query)
                | Q(status__icontains=query)
            )
        filtered_status_totals = {
            status.value: task_search_queryset.filter(status=status.value).count()
            for status in StatusChoices
        }
        task_queryset = task_search_queryset
        if selected_status:
            task_queryset = task_queryset.filter(status=selected_status)

        task_page = Paginator(task_queryset, 8).get_page(page_number)
        table_rows = [_decorate_task(task, now) for task in task_page.object_list]
        for task in table_rows:
            task.edit_url = reverse("task_edit", args=[task.pk])

        table_count = task_queryset.count()
        pagination = _build_pagination(dashboard_url, task_page, tab="tasks", q=query, status=selected_status)
        status_filters = _build_status_filters(dashboard_url, "tasks", query, selected_status, task_search_queryset.count(), filtered_status_totals)

        panel_title = "Tasks"
        panel_eyebrow = "Task Workspace"
        panel_copy = "Track every task with its status, category, priority, and deadline without leaving the task module."
        panel_action_label = "+ Add Task"
        panel_action_url = reverse("task_add")
        panel_stats = [
            {"label": "Tasks", "value": total_tasks},
            {"label": "Pending", "value": pending_tasks},
            {"label": "In Progress", "value": in_progress_tasks},
            {"label": "Completed", "value": completed_tasks},
        ]
        search_placeholder = "Search task title, description, category, priority, or status"

    elif active_tab == "subtasks":
        subtask_search_queryset = SubTask.objects.select_related(
            "parent_task", "parent_task__category", "parent_task__priority"
        ).order_by("-updated_at", "parent_task__title", "title")
        if query:
            subtask_search_queryset = subtask_search_queryset.filter(
                Q(title__icontains=query) | Q(parent_task__title__icontains=query) | Q(status__icontains=query)
            )
        filtered_status_totals = {
            status.value: subtask_search_queryset.filter(status=status.value).count()
            for status in StatusChoices
        }
        subtask_queryset = subtask_search_queryset
        if selected_status:
            subtask_queryset = subtask_queryset.filter(status=selected_status)

        subtask_page = Paginator(subtask_queryset, 8).get_page(page_number)
        table_rows = [_decorate_subtask(subtask) for subtask in subtask_page.object_list]
        for subtask in table_rows:
            subtask.edit_url = reverse("subtask_edit", args=[subtask.pk])

        table_count = subtask_queryset.count()
        pagination = _build_pagination(dashboard_url, subtask_page, tab="subtasks", q=query, status=selected_status)
        status_filters = _build_status_filters(dashboard_url, "subtasks", query, selected_status, subtask_search_queryset.count(), filtered_status_totals)

        panel_title = "Sub Tasks"
        panel_eyebrow = "Task Workspace"
        panel_copy = "Break parent tasks into execution units and keep each unit visible from the same workspace."
        panel_action_label = "+ Add Sub Task"
        panel_action_url = reverse("subtask_add")
        panel_stats = [
            {"label": "Subtasks", "value": total_subtasks},
            {"label": "Pending", "value": pending_subtasks},
            {"label": "In Progress", "value": in_progress_subtasks},
            {"label": "Completed", "value": completed_subtasks},
        ]
        search_placeholder = "Search subtask title, parent task, or status"

    elif active_tab == "categories":
        category_queryset = Category.objects.annotate(
            task_count=Count("tasks", distinct=True),
            open_count=Count("tasks", filter=Q(tasks__status__in=OPEN_STATUSES), distinct=True),
            completed_count=Count("tasks", filter=Q(tasks__status=StatusChoices.COMPLETED), distinct=True),
        ).order_by("-task_count", "name")
        if query:
            category_queryset = category_queryset.filter(name__icontains=query)

        category_page = Paginator(category_queryset, 8).get_page(page_number)
        table_rows = list(category_page.object_list)
        for category in table_rows:
            category.edit_url = reverse("category_edit", args=[category.pk])

        table_count = category_queryset.count()
        pagination = _build_pagination(dashboard_url, category_page, tab="categories", q=query)

        panel_title = "Categories"
        panel_eyebrow = "Task Workspace"
        panel_copy = "Review the task buckets that organize your work and see how many records each category carries."
        panel_action_label = "+ Add Category"
        panel_action_url = reverse("category_add")
        panel_stats = [
            {"label": "Categories", "value": total_categories},
            {"label": "Assigned Tasks", "value": total_tasks},
            {"label": "Active Buckets", "value": Category.objects.filter(tasks__status__in=OPEN_STATUSES).distinct().count()},
            {"label": "Completed Buckets", "value": Category.objects.filter(tasks__status=StatusChoices.COMPLETED).distinct().count()},
        ]
        search_placeholder = "Search category name"

    elif active_tab == "priorities":
        priority_queryset = Priority.objects.annotate(
            task_count=Count("tasks", distinct=True),
            open_count=Count("tasks", filter=Q(tasks__status__in=OPEN_STATUSES), distinct=True),
            completed_count=Count("tasks", filter=Q(tasks__status=StatusChoices.COMPLETED), distinct=True),
        ).order_by("-task_count", "name")
        if query:
            priority_queryset = priority_queryset.filter(name__icontains=query)

        priority_page = Paginator(priority_queryset, 8).get_page(page_number)
        table_rows = list(priority_page.object_list)
        for priority in table_rows:
            priority.edit_url = reverse("priority_edit", args=[priority.pk])

        table_count = priority_queryset.count()
        pagination = _build_pagination(dashboard_url, priority_page, tab="priorities", q=query)

        panel_title = "Priorities"
        panel_eyebrow = "Task Workspace"
        panel_copy = "Keep urgency levels consistent across the board and see how many tasks each level carries."
        panel_action_label = "+ Add Priority"
        panel_action_url = reverse("priority_add")
        panel_stats = [
            {"label": "Priorities", "value": total_priorities},
            {"label": "Tagged Tasks", "value": total_tasks},
            {"label": "Active Levels", "value": Priority.objects.filter(tasks__status__in=OPEN_STATUSES).distinct().count()},
            {"label": "Completed Levels", "value": Priority.objects.filter(tasks__status=StatusChoices.COMPLETED).distinct().count()},
        ]
        search_placeholder = "Search priority name"

    elif active_tab == "notes":
        note_queryset = Note.objects.select_related(
            "task", "task__category", "task__priority"
        ).order_by("-updated_at", "-created_at")
        if query:
            note_queryset = note_queryset.filter(
                Q(content__icontains=query) | Q(task__title__icontains=query)
            )

        note_page = Paginator(note_queryset, 8).get_page(page_number)
        table_rows = list(note_page.object_list)
        for note in table_rows:
            note.edit_url = reverse("note_edit", args=[note.pk])

        table_count = note_queryset.count()
        pagination = _build_pagination(dashboard_url, note_page, tab="notes", q=query)

        panel_title = "Notes"
        panel_eyebrow = "Knowledge Layer"
        panel_copy = "Review task notes, search captured context, and jump into edits when details change."
        panel_action_label = "+ Add Note"
        panel_action_url = reverse("note_add")
        panel_stats = [
            {"label": "Notes", "value": notes_count},
            {"label": "Tasks With Notes", "value": tasks_with_notes_count},
            {"label": "Added This Week", "value": recent_notes_count},
            {"label": "Tracked Tasks", "value": total_tasks},
        ]
        search_placeholder = "Search note content or task title"

    context = {
        "active_tab": active_tab,
        "main_nav": main_nav,
        "dashboard_url": dashboard_url,
        "today": today,
        "panel_title": panel_title,
        "panel_eyebrow": panel_eyebrow,
        "panel_copy": panel_copy,
        "panel_action_label": panel_action_label,
        "panel_action_url": panel_action_url,
        "dashboard_stats": dashboard_stats,
        "dashboard_summary_cards": dashboard_summary_cards,
        "status_flow": status_flow,
        "recent_task_updates": recent_task_updates,
        "upcoming_deadlines": upcoming_deadlines,
        "dashboard_categories": dashboard_categories,
        "dashboard_recent_notes": dashboard_recent_notes,
        "panel_stats": panel_stats,
        "status_filters": status_filters,
        "search_placeholder": search_placeholder,
        "query": query,
        "selected_status": selected_status,
        "table_rows": table_rows,
        "table_count": table_count,
        "pagination": pagination,
        "total_tasks": total_tasks,
        "notes_count": notes_count,
        "tasks_with_notes_count": tasks_with_notes_count,
        "open_tasks": open_tasks,
        "completion_rate": completion_rate,
        "due_today_count": due_today_count,
        "week_due_count": week_due_count,
        "overdue_tasks_count": overdue_tasks_count,
        "total_subtasks": total_subtasks,
    }
    return render(request, "hangarin/dashboard.html", context)


def _build_status_filters(dashboard_url, tab, query, selected_status, total_count, status_totals):
    filters = [
        {
            "label": "All",
            "count": total_count,
            "active": not selected_status,
            "url": _build_url(dashboard_url, tab=tab, q=query),
        }
    ]
    for status in StatusChoices:
        filters.append(
            {
                "label": status.label,
                "count": status_totals.get(status.value, 0),
                "active": selected_status == status.value,
                "url": _build_url(dashboard_url, tab=tab, q=query, status=status.value),
            }
        )
    return filters


def _build_pagination(base_url, page_obj, **params):
    if page_obj.paginator.num_pages <= 1:
        return None
    pagination = {
        "label": f"Page {page_obj.number} of {page_obj.paginator.num_pages}",
        "previous_url": "",
        "next_url": "",
    }
    if page_obj.has_previous():
        pagination["previous_url"] = _build_url(base_url, page=page_obj.previous_page_number(), **params)
    if page_obj.has_next():
        pagination["next_url"] = _build_url(base_url, page=page_obj.next_page_number(), **params)
    return pagination


def _build_url(base_url, **params):
    clean_params = {key: value for key, value in params.items() if value not in ("", None)}
    if not clean_params:
        return base_url
    return f"{base_url}?{urlencode(clean_params)}"


from django.utils import timezone

def _decorate_task(task, now):
    task.status_badge = STATUS_BADGE_CLASSES.get(task.status, "status-pill")
    task.priority_badge = PRIORITY_BADGE_CLASSES.get(
        task.priority.name.lower(),
        "priority-pill priority-pill-default",
    )
    task.deadline_local = timezone.localtime(task.deadline)
    task.progress_percent = _task_progress(task)
    task.is_overdue = task.deadline < now and task.status in OPEN_STATUSES

    if task.status == StatusChoices.COMPLETED:
        task.deadline_state = "Completed"
        task.deadline_state_class = "deadline-state deadline-state-complete"
    elif task.deadline_local.date() < now.date():
        task.deadline_state = "Overdue"
        task.deadline_state_class = "deadline-state deadline-state-danger"
    elif task.deadline_local.date() == now.date():
        task.deadline_state = "Due today"
        task.deadline_state_class = "deadline-state deadline-state-warning"
    else:
        task.deadline_state = "Upcoming"
        task.deadline_state_class = "deadline-state deadline-state-info"

    return task


def _decorate_subtask(subtask):
    subtask.status_badge = STATUS_BADGE_CLASSES.get(subtask.status, "status-pill")
    return subtask


def _task_progress(task):
    if getattr(task, "total_subtasks", 0):
        return round((task.completed_subtask_count / task.total_subtasks) * 100)
    if task.status == StatusChoices.COMPLETED:
        return 100
    if task.status == StatusChoices.IN_PROGRESS:
        return 50
    return 0


class HangarinBaseFormView(LoginRequiredMixin):
    template_name = "hangarin/entity_form.html"
    
    def get_success_url(self):
        url = reverse("dashboard")
        return f"{url}?tab={self.tab_name}"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["cancel_url"] = self.get_success_url()
        return context

# TASK VIEWS
class TaskCreateView(HangarinBaseFormView, CreateView):
    model = Task
    form_class = TaskForm
    tab_name = "tasks"
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Create Task"
        context["copy"] = "Add a new task to your workspace."
        return context

class TaskUpdateView(HangarinBaseFormView, UpdateView):
    model = Task
    form_class = TaskForm
    tab_name = "tasks"
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Edit Task"
        context["copy"] = "Update details for this task."
        return context

# SUBTASK VIEWS
class SubTaskCreateView(HangarinBaseFormView, CreateView):
    model = SubTask
    form_class = SubTaskForm
    tab_name = "subtasks"
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Create Sub Task"
        context["copy"] = "Add an execution unit to a parent task."
        return context

class SubTaskUpdateView(HangarinBaseFormView, UpdateView):
    model = SubTask
    form_class = SubTaskForm
    tab_name = "subtasks"
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Edit Sub Task"
        context["copy"] = "Update details for this sub task."
        return context

# CATEGORY VIEWS
class CategoryCreateView(HangarinBaseFormView, CreateView):
    model = Category
    form_class = CategoryForm
    tab_name = "categories"
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Create Category"
        context["copy"] = "Add a new organizational bucket."
        return context

class CategoryUpdateView(HangarinBaseFormView, UpdateView):
    model = Category
    form_class = CategoryForm
    tab_name = "categories"
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Edit Category"
        context["copy"] = "Update category definition."
        return context

# PRIORITY VIEWS
class PriorityCreateView(HangarinBaseFormView, CreateView):
    model = Priority
    form_class = PriorityForm
    tab_name = "priorities"
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Create Priority"
        context["copy"] = "Define a new urgency level."
        return context

class PriorityUpdateView(HangarinBaseFormView, UpdateView):
    model = Priority
    form_class = PriorityForm
    tab_name = "priorities"
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Edit Priority"
        context["copy"] = "Update priority settings."
        return context

# NOTE VIEWS
class NoteCreateView(HangarinBaseFormView, CreateView):
    model = Note
    form_class = NoteForm
    tab_name = "notes"
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Create Note"
        context["copy"] = "Add context or details to a task."
        return context

class NoteUpdateView(HangarinBaseFormView, UpdateView):
    model = Note
    form_class = NoteForm
    tab_name = "notes"
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Edit Note"
        context["copy"] = "Update recorded task notes."
        return context
