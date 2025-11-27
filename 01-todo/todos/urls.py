from django.urls import path
from .views import (
    TodoListView,
    TodoCreateView,
    TodoUpdateView,
    TodoDeleteView,
    TodoResolveView,
)

urlpatterns = [
    path('', TodoListView.as_view(), name='todo-list'),
    path('create/', TodoCreateView.as_view(), name='todo-create'),
    path('<int:pk>/edit/', TodoUpdateView.as_view(), name='todo-edit'),
    path('<int:pk>/delete/', TodoDeleteView.as_view(), name='todo-delete'),
    path('<int:pk>/resolve/', TodoResolveView.as_view(), name='todo-resolve'),
]
