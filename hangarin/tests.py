from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .models import Category, Note, Priority, StatusChoices, SubTask, Task


class ModelBehaviorTests(TestCase):
    def setUp(self):
        self.category = Category.objects.create(name="Work")
        self.priority = Priority.objects.create(name="High")

    def test_string_representations(self):
        task = Task.objects.create(
            title="Prepare project report",
            description="Draft the weekly status report.",
            deadline=timezone.now(),
            status=StatusChoices.PENDING,
            category=self.category,
            priority=self.priority,
        )
        subtask = SubTask.objects.create(
            parent_task=task,
            title="Outline the report",
            status=StatusChoices.IN_PROGRESS,
        )
        note = Note.objects.create(task=task, content="Collect the latest metrics.")

        self.assertEqual(str(self.category), "Work")
        self.assertEqual(str(self.priority), "High")
        self.assertEqual(str(task), "Prepare project report")
        self.assertEqual(str(subtask), "Outline the report")
        self.assertEqual(str(note), "Note for Prepare project report")

    def test_plural_names_are_human_readable(self):
        self.assertEqual(Category._meta.verbose_name_plural, "Categories")
        self.assertEqual(Priority._meta.verbose_name_plural, "Priorities")


class SeedCommandTests(TestCase):
    def test_seed_command_creates_reference_and_fake_data(self):
        call_command("seed_hangarin", tasks=3, notes_per_task=1, subtasks_per_task=2)

        self.assertEqual(Category.objects.count(), 5)
        self.assertEqual(Priority.objects.count(), 5)
        self.assertEqual(Task.objects.count(), 3)
        self.assertEqual(Note.objects.count(), 3)
        self.assertEqual(SubTask.objects.count(), 6)


class DashboardViewTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_superuser(
            username="richo",
            password="testpass123",
            email="richo@example.com",
        )
        self.category = Category.objects.create(name="Projects")
        self.priority = Priority.objects.create(name="critical")
        self.task = Task.objects.create(
            title="Launch client dashboard",
            description="Finalize the UI and connect the management workflows.",
            deadline=timezone.now() + timedelta(days=1),
            status=StatusChoices.IN_PROGRESS,
            category=self.category,
            priority=self.priority,
        )
        SubTask.objects.create(
            parent_task=self.task,
            title="Build summary widgets",
            status=StatusChoices.COMPLETED,
        )
        SubTask.objects.create(
            parent_task=self.task,
            title="Wire admin shortcuts",
            status=StatusChoices.IN_PROGRESS,
        )
        Note.objects.create(task=self.task, content="Need sign-off from the project lead.")

    def test_login_page_renders(self):
        response = self.client.get(reverse("login"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Hangarin")
        self.assertContains(response, "Enter Dashboard")
        self.assertContains(response, "Continue with Google")
        self.assertContains(response, "Continue with GitHub")
        self.assertContains(
            response,
            "Google and GitHub sign-in are disabled until social login is enabled on the server.",
        )

    def test_dashboard_requires_login(self):
        response = self.client.get(reverse("dashboard"))

        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("login"), response.url)

    def test_dashboard_renders_sidebar_and_overview_content(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("dashboard"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Dashboard")
        self.assertContains(response, "Task")
        self.assertContains(response, "Notes")
        self.assertContains(response, "Task Status Overview")
        self.assertContains(response, "Latest Task Updates")
        self.assertContains(response, "Launch client dashboard")

    def test_task_workspace_renders_internal_sections_and_filters(self):
        self.client.force_login(self.user)
        completed_task = Task.objects.create(
            title="Archive completed sprint",
            description="Wrap up work from the last iteration.",
            deadline=timezone.now(),
            status=StatusChoices.COMPLETED,
            category=self.category,
            priority=self.priority,
        )

        response = self.client.get(
            reverse("dashboard"),
            {
                "tab": "tasks",
                "status": StatusChoices.COMPLETED,
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Tasks")
        self.assertContains(response, completed_task.title)
        self.assertContains(
            response,
            f"{reverse('dashboard')}?tab=tasks&amp;status=Completed",
            html=False,
        )

    def test_notes_tab_renders_note_feed(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("dashboard"), {"tab": "notes"})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Notes")
        self.assertContains(response, "Need sign-off from the project lead.")

    def test_task_subsections_render_records(self):
        self.client.force_login(self.user)
        response = self.client.get(
            reverse("dashboard"),
            {"tab": "categories"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Categories")
        self.assertContains(response, self.category.name)

        response = self.client.get(
            reverse("dashboard"),
            {"tab": "priorities"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Priorities")
        self.assertContains(response, self.priority.name.title())
