from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from .models import Todo
from .forms import TodoForm


class TodoListView(ListView):
    model = Todo
    template_name = 'home.html'
    context_object_name = 'todos'


class TodoCreateView(CreateView):
    model = Todo
    form_class = TodoForm
    template_name = 'todos/todo_form.html'
    success_url = reverse_lazy('todo-list')


class TodoUpdateView(UpdateView):
    model = Todo
    form_class = TodoForm
    template_name = 'todos/todo_form.html'
    success_url = reverse_lazy('todo-list')


class TodoDeleteView(DeleteView):
    model = Todo
    template_name = 'todos/todo_confirm_delete.html'
    success_url = reverse_lazy('todo-list')


class TodoResolveView(View):
    def post(self, request, pk):
        todo = get_object_or_404(Todo, pk=pk)
        todo.resolved = not todo.resolved
        todo.save()
        return redirect('todo-list')


class TodoBulkDeleteView(View):
    def post(self, request):
        selected_ids = request.POST.getlist('selected_todos')
        if selected_ids:
            Todo.objects.filter(pk__in=selected_ids).delete()
        return redirect('todo-list')
