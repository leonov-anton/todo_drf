from rest_framework import serializers
from django.utils import timezone
from .models import Task, Category


class TaskSerializer(serializers.ModelSerializer):
    category = serializers.CharField(max_length=20, label='Категория', source='category.name')

    class Meta:
        model = Task
        fields = ['id', 'title', 'content', 'deadline', 'category', 'status', 'priority']
        read_only_fields = ['id', 'status']

    def validate(self, data):
        if data['deadline'] < timezone.now():
            raise serializers.ValidationError('Это время уже прошло')
        return data

    def create(self, validated_data):
        user = self.context['request'].user
        category, created = Category.objects.get_or_create(name=validated_data.pop('category')['name'])
        if not user.category_set.filter(name=category.name).exists():
            category.user.add(user)
            category.save()
        task = Task.objects.create(**validated_data, category=category)
        return task


class TaskDeteilSerializer(serializers.ModelSerializer):
    category = serializers.CharField(max_length=20, label='Категория', source='category.name')

    class Meta:
        model = Task
        fields = ['id', 'title', 'content', 'deadline', 'category', 'status', 'priority']

    def validate(self, data):
        if data['deadline'] < timezone.now():
            raise serializers.ValidationError('Это время уже прошло')
        return data

    def update(self, instance, validated_data):
        user = self.context['request'].user
        category, created = Category.objects.get_or_create(name=validated_data.get('category')['name'])
        if not user.category_set.filter(name=category.name).exists():
            category.user.add(user)
            category.save()
        instance.title = validated_data.get('title', instance.title)
        instance.content = validated_data.get('content', instance.content)
        instance.deadline = validated_data.get('deadline', instance.deadline)
        instance.category = category
        instance.status = validated_data.get('status', instance.status)
        instance.priority = validated_data.get('priority', instance.priority)
        instance.save()
        return instance


class TaskFieldUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields = ['status', 'priority', 'done_time']


class TaskCopySerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields = '__all__'


class CategorySerializer(serializers.ModelSerializer):
    """
    Удаление категорий не выполняется, т.к. категории общие для многих пользователей при совпадении имен категорий.
    Удаляется только свзять категории и пользователя.
    """
    class Meta:
        model = Category
        fields = ['id', 'name']

    def create(self, validated_data):
        user = self.context['request'].user
        category, created = Category.objects.get_or_create(name=validated_data.get('name'))
        category.user.add(user)
        category.save()
        return category

    def update(self, instance, validated_data):
        user = self.context['request'].user
        new_category, created = Category.objects.get_or_create(name=validated_data.get('name'))
        Task.objects.select_related('owner', 'category').filter(category=instance, owner=user)\
            .update(category=new_category)
        new_category.user.add(user)
        new_category.save()
        instance.user.remove(user)
        instance.save()
        return new_category



