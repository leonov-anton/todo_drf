from django.shortcuts import get_object_or_404
from django.db.models import Q
from rest_framework import generics, permissions, views, response, status, filters
import django_filters.rest_framework
from rest_framework.pagination import PageNumberPagination
from datetime import datetime

from .serializers import TaskSerializer, TaskDeteilSerializer, TaskFieldUpdateSerializer, CategorySerializer, \
    TaskCopySerializer
from .models import Task, Category
from .permissions import IsOwner


class TaskList(generics.ListCreateAPIView):
    serializer_class = TaskSerializer
    pagination_class = PageNumberPagination
    filter_backends = [filters.SearchFilter]
    search_fields = ['title', 'content', 'category__name']
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

    def get_queryset(self):
        return Task.objects.select_related('category').filter(owner=self.request.user)\
            .only('id', 'title', 'content', 'deadline', 'category__name', 'status', 'priority')


class TaskDatePeriodList(generics.ListAPIView):
    """
    просмотр всех задач пользователя
    """
    serializer_class = TaskSerializer
    pagination_class = PageNumberPagination
    lookup_field = ['sdate', 'edate']
    filter_backends = [filters.SearchFilter]
    search_fields = ['title', 'content', 'category__name']
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        sdate = self.kwargs.get('sdate')
        edate = self.kwargs.get('edate')
        return Task.objects.select_related('category').filter(Q(owner=self.request.user)
                                                              & Q(deadline__range=[sdate, edate]))\
            .only('id', 'title', 'content', 'deadline', 'category__name', 'status', 'priority')


class TaskDetail(generics.RetrieveUpdateDestroyAPIView):
    """
    просмотр деталей задачи, удаление, обновление.
    """
    serializer_class = TaskDeteilSerializer
    permission_classes = [IsOwner]

    def get_queryset(self):
        return Task.objects.select_related('owner', 'category').filter(owner=self.request.user)\
            .only('id', 'title', 'owner__id', 'content', 'deadline', 'category__name', 'status', 'priority')


class TaskDone(views.APIView):
    """
    закрытие задачи
    """
    permission_classes = [IsOwner]

    def patch(self, request, pk):
        task = get_object_or_404(Task, pk=pk)
        self.check_object_permissions(self.request, task)
        data = {'status': True, 'done_time': datetime.now()}
        serializer = TaskFieldUpdateSerializer(task, data=data, partial=True)

        if serializer.is_valid():
            serializer.save()
            return response.Response(serializer.data)
        return response.Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class TaskPriority(views.APIView):
    """
    изменение приоритета задачи
    """
    permission_classes = [IsOwner]

    def patch(self, request, priority, pk):
        task = get_object_or_404(Task, pk=pk)
        self.check_object_permissions(self.request, task)
        data = {'priority': priority}
        serializer = TaskFieldUpdateSerializer(task, data=data, partial=True)

        if serializer.is_valid():
            serializer.save()
            return response.Response(serializer.data)
        return response.Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class TaskCopy(views.APIView):
    """
    копирование задачи
    """
    permission_classes = [IsOwner]

    def post(self, request, pk, format=None):
        task = get_object_or_404(Task, pk=pk)
        self.check_object_permissions(self.request, task)
        data = task.__dict__
        data.pop('id')
        owner_id = data.pop('owner_id')
        category_id = data.pop('category_id')
        data['owner'] = owner_id
        data['category'] = category_id
        serializer = TaskCopySerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return response.Response(serializer.data)
        return response.Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserCategory(generics.ListCreateAPIView):
    """
    Просмотр и создание пользовательских категорий задач
    """
    serializer_class = CategorySerializer
    pagination_class = PageNumberPagination
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Category.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save()
        category_name = serializer.data.get('name')
        category = Category.objects.get(name=category_name)
        category.user.add(self.request.user)


class UserCategoryDetail(generics.RetrieveUpdateDestroyAPIView):
    """
    удаление и изменение имени категории пользователя
    """
    serializer_class = CategorySerializer
    queryset = Category.objects.all()
    permission_classes = [permissions.IsAuthenticated]

    def delete(self, request, *args, **kwargs):
        # так же удалит все задачи в этой категории
        category = self.get_object()
        Task.objects.filter(category=category, owner=self.request.user).delete()
        category.user.remove(request.user)
        return response.Response(status=status.HTTP_204_NO_CONTENT)



