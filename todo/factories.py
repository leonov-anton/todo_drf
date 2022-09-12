import factory
import datetime
from factory import fuzzy
from .models import Task, Category
from django.contrib.auth.models import User


class CategoryFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Category

    name = fuzzy.FuzzyText(length=20)


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User

    username = factory.Sequence(lambda n: f'testuser{n}')
    email = factory.Sequence(lambda n: f'testuser{n}@mail.com')
    password = factory.Sequence(lambda n: f'testuser{n}')


class TaskFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Task

    title = factory.Sequence(lambda n: f'Задача_{n}')
    content = fuzzy.FuzzyText(length=100)
    created = fuzzy.FuzzyDateTime(datetime.datetime.now(tz=datetime.timezone.utc))
    deadline = fuzzy.FuzzyDateTime(datetime.datetime.now(tz=datetime.timezone.utc),
                                   datetime.datetime(2022, 12, 31, 20, tzinfo=datetime.timezone.utc))
    category = factory.SubFactory(CategoryFactory)
    owner = factory.SubFactory(UserFactory)
