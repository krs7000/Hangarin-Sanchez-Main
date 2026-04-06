import random

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from faker import Faker

from hangarin.models import Category, Note, Priority, StatusChoices, SubTask, Task


DEFAULT_CATEGORIES = ("Work", "School", "Personal", "Finance", "Projects")
DEFAULT_PRIORITIES = ("high", "medium", "low", "critical", "optional")


class Command(BaseCommand):
    help = (
        "Populate the database with the required default Category and Priority "
        "records, then generate fake Task, Note, and SubTask data."
    )

    def add_arguments(self, parser):
        parser.add_argument("--tasks", type=int, default=10)
        parser.add_argument("--notes-per-task", type=int, default=2)
        parser.add_argument("--subtasks-per-task", type=int, default=3)

    def handle(self, *args, **options):
        fake = Faker()
        tasks_to_create = options["tasks"]
        notes_per_task = options["notes_per_task"]
        subtasks_per_task = options["subtasks_per_task"]

        with transaction.atomic():
            categories = [
                Category.objects.get_or_create(name=name)[0]
                for name in DEFAULT_CATEGORIES
            ]
            priorities = [
                Priority.objects.get_or_create(name=name)[0]
                for name in DEFAULT_PRIORITIES
            ]

            for _ in range(tasks_to_create):
                task = Task.objects.create(
                    title=fake.sentence(nb_words=5),
                    description=fake.paragraph(nb_sentences=3),
                    deadline=self._aware_datetime(fake),
                    status=fake.random_element(elements=StatusChoices.values),
                    category=random.choice(categories),
                    priority=random.choice(priorities),
                )

                for _ in range(notes_per_task):
                    Note.objects.create(
                        task=task,
                        content=fake.paragraph(nb_sentences=3),
                    )

                for _ in range(subtasks_per_task):
                    SubTask.objects.create(
                        parent_task=task,
                        title=fake.sentence(nb_words=5),
                        status=fake.random_element(elements=StatusChoices.values),
                    )

        self.stdout.write(
            self.style.SUCCESS(
                "Seeded categories, priorities, tasks, notes, and subtasks."
            )
        )

    def _aware_datetime(self, fake):
        deadline = fake.date_time_this_month()
        if timezone.is_naive(deadline):
            return timezone.make_aware(deadline)
        return deadline
