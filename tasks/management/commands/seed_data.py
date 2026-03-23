from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from faker import Faker
from tasks.models import Priority, Category, Task, SubTask, Note
import random

fake = Faker()


class Command(BaseCommand):
    help = 'Seed the database with initial data'

    def handle(self, *args, **kwargs):
        self.stdout.write('Seeding database...')

        # Create superuser if not exists
        if not User.objects.filter(username='admin').exists():
            User.objects.create_superuser('admin', 'admin@hangarin.com', 'admin123')
            self.stdout.write(self.style.SUCCESS('Superuser created: admin / admin123'))

        # Create a demo user
        demo_user, _ = User.objects.get_or_create(username='demo')
        demo_user.set_password('demo123')
        demo_user.save()
        admin_user = User.objects.get(username='admin')
        self.stdout.write(self.style.SUCCESS('Demo user: demo / demo123'))

        # Priorities
        priority_names = ['High', 'Medium', 'Low', 'Critical', 'Optional']
        priorities = []
        for name in priority_names:
            p, _ = Priority.objects.get_or_create(name=name)
            priorities.append(p)
        self.stdout.write(self.style.SUCCESS('Priorities seeded.'))

        # Categories
        category_names = ['Work', 'School', 'Personal', 'Finance', 'Projects']
        categories = []
        for name in category_names:
            c, _ = Category.objects.get_or_create(name=name)
            categories.append(c)
        self.stdout.write(self.style.SUCCESS('Categories seeded.'))

        # Tasks for demo user
        for _ in range(20):
            task = Task.objects.create(
                title=fake.sentence(nb_words=5),
                description=fake.paragraph(nb_sentences=3),
                deadline=timezone.make_aware(fake.date_time_this_month()),
                status=fake.random_element(elements=["Pending", "In Progress", "Completed"]),
                category=fake.random_element(elements=categories),
                priority=fake.random_element(elements=priorities),
                user=fake.random_element(elements=list(User.objects.all())),
            )

            # SubTasks
            for _ in range(random.randint(1, 3)):
                SubTask.objects.create(
                    parent_task=task,
                    title=fake.sentence(nb_words=4),
                    status=fake.random_element(elements=["Pending", "In Progress", "Completed"]),
                )

            # Notes
            for _ in range(random.randint(1, 2)):
                Note.objects.create(
                    task=task,
                    content=fake.paragraph(nb_sentences=2),
                )

        self.stdout.write(self.style.SUCCESS('Tasks, SubTasks, and Notes seeded.'))
        self.stdout.write(self.style.SUCCESS('Database seeding complete!'))
