from datetime import datetime
from django.urls import path, register_converter

from .views import TaskList, TaskDatePeriodList, TaskDetail, TaskDone, TaskPriority, UserCategory, UserCategoryDetail, \
    TaskCopy


class DateConverter:
    regex = r'\d{1,2}-\d{1,2}-\d{4}'
    format = '%d-%m-%Y'

    def to_python(self, value):
        return datetime.strptime(value, self.format).date()

    def to_url(self, value):
        return value.strftime(self.format)


register_converter(DateConverter, 'date')

urlpatterns = [
    path('task/', TaskList.as_view()),
    path('task/<date:sdate>/<date:edate>/', TaskDatePeriodList.as_view()),
    path('task/<int:pk>/', TaskDetail.as_view()),
    path('task/<int:pk>/done/', TaskDone.as_view()),
    path('task/<int:pk>/prior/<str:priority>/', TaskPriority.as_view()),
    path('task/category/', UserCategory.as_view()),
    path('task/category/<int:pk>/', UserCategoryDetail.as_view()),
    path('task/<int:pk>/copy/', TaskCopy.as_view()),
]
