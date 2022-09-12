import pytest
import json
import factory
from django.contrib.auth.models import User

from .factories import TaskFactory, CategoryFactory
from .models import Task, Category
from .serializers import TaskSerializer, TaskDeteilSerializer, CategorySerializer


@pytest.fixture
def api_client():
    from rest_framework.test import APIClient
    return APIClient()


@pytest.fixture
def create_user(db, django_user_model):
    def make_user(**kwargs):
        kwargs['password'] = '1q2w3e4r'
        return django_user_model.objects.create(**kwargs)
    return make_user


@pytest.fixture
def api_client_with_credentials(db, create_user, api_client):
    user = create_user(username='testuser')
    api_client.force_authenticate(user=user)
    yield api_client
    api_client.force_authenticate(user=None)


class TestTaskList:
    endpoint = '/task/'

    def test_unauthorized_request(self, api_client):
        """
        тест запроса списка задач от неавторизированного пользователя
        """
        response = api_client.get(self.endpoint)

        assert response.status_code == 403

    def test_authorized_request(self, api_client_with_credentials):
        """
        тест запроса списка задач от авторизированного пользователя
        """
        tasks = TaskFactory.create_batch(3)
        for task in tasks:
            task.owner = User.objects.get(username='testuser')
            task.save()
        response = api_client_with_credentials.get(self.endpoint)

        assert response.status_code == 200
        assert len(json.loads(response.content)) == 3

    def test_tasks_search(self, api_client_with_credentials):
        """
        тест запроса списка задач c поиском
        """
        tasks = TaskFactory.create_batch(3)
        for task in tasks:
            task.owner = User.objects.get(username='testuser')
            task.save()
        search = tasks[0].title[5:]
        response = api_client_with_credentials.get(f'{self.endpoint}?search={search}')

        assert response.status_code == 200
        assert json.loads(response.content)[0]['id'] == tasks[0].id


    def test_create(self, api_client_with_credentials):
        """
        тест post запроса от авторизированног опользователя
        """
        task = TaskFactory.build()
        data = {'title': task.title, 'content': task.content, 'deadline': task.deadline, 'created': task.created,
                'category': task.category.name, 'owner': task.owner.id, 'status': task.status,
                'priority': task.priority}
        response = api_client_with_credentials.post(self.endpoint, data=data, format='json')

        assert response.status_code == 201
        assert Task.objects.get(title=task.title)


class TestDatePeriodList:
    endpoint = '/task/01-09-2022/12-12-2022/'

    def test_unauthorized_request(self, api_client):
        """
        тест запроса списка задач за период от неавторизированного пользователя
        """
        response = api_client.get(self.endpoint)

        assert response.status_code == 403

    def test_list_date(self, api_client_with_credentials):
        """
        тест запроса списка задач за период
        """
        tasks = TaskFactory.create_batch(3)
        for task in tasks:
            task.owner = User.objects.get(username='testuser')
            task.save()
        response = api_client_with_credentials.get(self.endpoint)

        assert response.status_code == 200


class TestTaskDetail:
    endpoint = '/task/'

    def test_retrieve(self, api_client_with_credentials):
        """
        Тест запроса задачи
        """
        task = TaskFactory()
        task.owner = User.objects.get(username='testuser')
        task.save()
        response = api_client_with_credentials.get(f'{self.endpoint}{task.id}/')

        assert response.status_code == 200
        assert json.loads(response.content)['title'] == task.title

    def test_update(self, api_client_with_credentials):
        """
        Тест обновления задачи
        """
        task_old = TaskFactory()
        task_new = TaskFactory.build()
        task_old.owner = User.objects.get(username='testuser')
        task_old.save()
        data = {'title': task_new.title, 'category': task_new.category.name, 'content': task_new.content,
                'deadline': task_new.deadline, 'status': task_old.status, 'priority': task_old.priority}
        response = api_client_with_credentials.put(f'{self.endpoint}{task_old.id}/', data=data, format='json')

        assert response.status_code == 200
        assert json.loads(response.content)['title'] == task_new.title

    def test_delete(self, api_client_with_credentials):
        """
        Тест удаления задачи
        """
        task1 = TaskFactory()
        task2 = TaskFactory()
        task1.owner = User.objects.get(username='testuser')
        task1.save()
        response = api_client_with_credentials.delete(f'{self.endpoint}{task1.id}/')

        assert response.status_code == 204
        assert len(Task.objects.all()) == 1

    def test_retrieve_another_owner(self, api_client_with_credentials):
        """
        Тест запроса чужой задачи
        """
        task = TaskFactory()
        response = api_client_with_credentials.get(f'{self.endpoint}{task.id}/')

        assert response.status_code == 404

    def test_update_another_owner(self, api_client_with_credentials):
        """
        Тест обновления чужой задачи
        """
        task_old = TaskFactory()
        task_new = TaskFactory.build()
        data = {'title': task_new.title, 'category': task_new.category.name, 'content': task_new.content,
                'deadline': task_new.deadline, 'status': task_old.status, 'priority': task_old.priority}
        response = api_client_with_credentials.put(f'{self.endpoint}{task_old.id}/', data=data, format='json')

        assert response.status_code == 404

    def test_delete_another_owner(self, api_client_with_credentials):
        """
        Тест удаления чужой задачи
        """
        task = TaskFactory()
        response = api_client_with_credentials.delete(f'{self.endpoint}{task.id}/')

        assert response.status_code == 404


class TestTaskDone:
    endpoint = '/task/'

    def test_done(self, api_client_with_credentials):
        """
        Тест выполения задачи
        """
        task = TaskFactory()
        task.owner = User.objects.get(username='testuser')
        task.save()
        response = api_client_with_credentials.patch(f'{self.endpoint}{task.id}/done/')

        assert response.status_code == 200
        assert json.loads(response.content)['status']
        assert json.loads(response.content)['done_time']

    def test_done_another_owner(self, api_client_with_credentials):
        """
        Тест выполения чужой задачи
        """
        task = TaskFactory()
        response = api_client_with_credentials.patch(f'{self.endpoint}{task.id}/done/')

        assert response.status_code == 403


class TestTaskPriority:
    endpoint = '/task/'

    def test_priority(self, api_client_with_credentials):
        """
        Тест изменения приоритета задачи
        """
        task = TaskFactory()
        task.owner = User.objects.get(username='testuser')
        task.save()
        new_prior = 'low'
        response = api_client_with_credentials.patch(f'{self.endpoint}{task.id}/prior/{new_prior}/')

        assert response.status_code == 200
        assert json.loads(response.content)['priority'] == 'low'

    def test_priority_another_owner(self, api_client_with_credentials):
        """
        Тест изменения приоритета чужой задачи
        """
        task = TaskFactory()
        new_prior = 'low'
        response = api_client_with_credentials.patch(f'{self.endpoint}{task.id}/prior/{new_prior}/')

        assert response.status_code == 403


class TestTaskCopy:
    endpoint = '/task/'

    def test_task_copy(self, api_client_with_credentials):
        """
        Тест копирования задачи
        """
        task = TaskFactory()
        task.owner = User.objects.get(username='testuser')
        task.save()
        task_title = task.title
        response = api_client_with_credentials.post(f'{self.endpoint}{task.id}/copy/')

        assert response.status_code == 200
        assert Task.objects.filter(title=task_title).count() == 2

    def test_task_copy_another_owner(self, api_client_with_credentials):
        """
        Тест копирования чужой задачи
        """
        task = TaskFactory()
        response = api_client_with_credentials.post(f'{self.endpoint}{task.id}/copy/')

        assert response.status_code == 403


class TestUserCategory:
    endpoint = '/task/category/'

    def test_unauthorized_request(self, api_client):
        """
        Тест запроса списка категорий от неавторизированного пользователя
        """
        response = api_client.get(self.endpoint)

        assert response.status_code == 403

    def test_authorized_request(self, api_client_with_credentials):
        """
        Тест запроса списка категорий от авторизированного пользователя, должен получить только категорию в которую он
        добавлен
        """
        category_1 = CategoryFactory()
        category_2 = CategoryFactory()
        user = User.objects.get(username='testuser')
        category_2.user.add(user)
        category_2.save()
        response = api_client_with_credentials.get(self.endpoint)

        assert response.status_code == 200
        assert len(Category.objects.filter(user=user)) == 1

    def test_create(self, api_client_with_credentials):
        """
        Тест post запроса от авторизированног опользователя
        """
        category = CategoryFactory.build()
        data = {'name': category.name}
        response = api_client_with_credentials.post(f'{self.endpoint}', data=data, format='json')

        assert response.status_code == 201
        assert Category.objects.all().count() == 1


class TestUserCategoryDetail:
    endpoint = '/task/category/'

    def test_retrieve(self, api_client_with_credentials):
        """
        Тест получения информации об одной записи
        """
        category = CategoryFactory()
        expected_json = {'id': category.id, 'name': category.name}
        response = api_client_with_credentials.get(f'{self.endpoint}{category.id}/')

        assert response.status_code == 200
        assert json.loads(response.content) == expected_json

    def test_update(self, api_client_with_credentials):
        """
        Тест изменений имени категории
        """
        category_old = CategoryFactory()
        category_new = CategoryFactory.build()
        data = {'name': category_new.name}
        response = api_client_with_credentials.put(f'{self.endpoint}{category_old.id}/', data=data, format='json')

        assert response.status_code == 200
        assert json.loads(response.content)['name'] == category_new.name

    def test_delete(self, api_client_with_credentials):
        """
        Тест "удалени" категории для пользователя. Самого удаления не происходит, пользователь просто удаляется из
        поля user
        """
        category = CategoryFactory()
        user = User.objects.get(username='testuser')
        category.user.add(user)
        category.save()
        response = api_client_with_credentials.delete(f'{self.endpoint}{category.id}/')

        assert response.status_code == 204
        assert category
        assert not user.category_set.filter(name=category.name).exists()


class TestTaskSerializer:

    def test_serialize_model(self):
        task = TaskFactory.build()
        serializer = TaskSerializer(task)

        assert serializer.data

    def test_serialize_data(self):
        serialized_data = factory.build(dict, FACTORY_CLASS=TaskFactory)
        serialized_data['category'] = serialized_data['category'].name
        serializer = TaskSerializer(data=serialized_data)

        assert serializer.is_valid(raise_exception=True)
        assert serializer.errors == {}


class TestDetailTaskSerializer:

    def test_serialize_model(self):
        task = TaskFactory.build()
        serializer = TaskDeteilSerializer(task)

        assert serializer.data

    def test_serialize_data(self):
        serialized_data = factory.build(dict, FACTORY_CLASS=TaskFactory)
        serialized_data['category'] = serialized_data['category'].name
        serializer = TaskDeteilSerializer(data=serialized_data)

        assert serializer.is_valid(raise_exception=True)
        assert serializer.errors == {}


class TestCategorySerializer:

    def test_serialize_model(self):
        task = CategoryFactory.build()
        serializer = CategorySerializer(task)

        assert serializer.data

    def test_serialize_data(self):
        serialized_data = factory.build(dict, FACTORY_CLASS=CategoryFactory)
        serializer = CategorySerializer(data=serialized_data)

        assert serializer.is_valid(raise_exception=True)
        assert serializer.errors == {}
