"""
Tests for Todo views.

This module tests the presentation and routing layer,
ensuring views handle HTTP requests/responses correctly.
"""

from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta
from ..models import Todo
from ..forms import TodoForm
from .conftest import create_todo, create_todo_with_due_date, BaseTestCase


class TodoListViewTests(BaseTestCase):
    """Tests for the todo list view."""

    def setUp(self):
        """Set up test data."""
        super().setUp()
        self.list_url = reverse('todo-list')

    def test_list_view_get_request(self):
        """Test GET request to list view returns 200."""
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, 200)

    def test_list_view_uses_correct_template(self):
        """Test that list view uses home.html template."""
        response = self.client.get(self.list_url)
        self.assertTemplateUsed(response, 'home.html')

    def test_list_view_displays_all_todos(self):
        """Test that list view returns all created todos."""
        todo1 = create_todo(title="Task 1")
        todo2 = create_todo(title="Task 2")
        todo3 = create_todo(title="Task 3")

        response = self.client.get(self.list_url)
        todos = response.context['todos']

        self.assertEqual(len(todos), 3)
        self.assertIn(todo1, todos)
        self.assertIn(todo2, todos)
        self.assertIn(todo3, todos)

    def test_list_view_empty(self):
        """Test list view when there are no todos."""
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['todos']), 0)

    def test_list_view_shows_resolved_todos(self):
        """Test that resolved todos appear in list view."""
        resolved_todo = create_todo(title="Done Task", resolved=True)
        response = self.client.get(self.list_url)
        self.assertIn(resolved_todo, response.context['todos'])

    def test_list_view_todos_ordered_by_due_date(self):
        """Test that todos in list view are ordered by due date."""
        create_todo(title="No Date", due_date=None)
        create_todo_with_due_date(days_from_now=30)
        create_todo_with_due_date(days_from_now=5)

        response = self.client.get(self.list_url)
        todos = list(response.context['todos'])

        # First should be without due date
        self.assertIsNone(todos[0].due_date)


class TodoCreateViewTests(BaseTestCase):
    """Tests for creating todos."""

    def setUp(self):
        """Set up test URLs."""
        super().setUp()
        self.create_url = reverse('todo-create')
        self.list_url = reverse('todo-list')

    def test_create_view_get_request(self):
        """Test GET request to create view displays the form."""
        response = self.client.get(self.create_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'todos/todo_form.html')
        self.assertIsInstance(response.context['form'], TodoForm)

    def test_create_todo_with_title_only(self):
        """Test creating todo with only title (required field)."""
        data = {'title': 'My First Todo'}
        response = self.client.post(self.create_url, data)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(Todo.objects.count(), 1)
        todo = Todo.objects.first()
        self.assertEqual(todo.title, 'My First Todo')

    def test_create_todo_with_all_fields(self):
        """Test creating todo with all fields."""
        due_date = (timezone.now() + timedelta(days=5)).date()
        data = {
            'title': 'Complete Todo',
            'description': 'This is detailed',
            'due_date': due_date
        }
        response = self.client.post(self.create_url, data)

        todo = Todo.objects.first()
        self.assertEqual(todo.title, 'Complete Todo')
        self.assertEqual(todo.description, 'This is detailed')
        self.assertEqual(todo.due_date, due_date)

    def test_create_todo_missing_title(self):
        """Test that creating todo without title fails."""
        data = {'description': 'No title provided'}
        response = self.client.post(self.create_url, data)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(Todo.objects.count(), 0)
        self.assertFormError(response, 'form', 'title', 'This field is required.')

    def test_create_todo_redirects_to_list(self):
        """Test redirect after successful creation."""
        data = {'title': 'New Todo'}
        response = self.client.post(self.create_url, data, follow=False)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, self.list_url)

    def test_create_todo_with_empty_description(self):
        """Test creating todo with empty description (optional field)."""
        data = {'title': 'No Description', 'description': ''}
        response = self.client.post(self.create_url, data)

        todo = Todo.objects.first()
        self.assertEqual(todo.description, '')

    def test_create_todo_with_empty_due_date(self):
        """Test creating todo without due date (optional field)."""
        data = {'title': 'No Due Date', 'due_date': ''}
        response = self.client.post(self.create_url, data)

        todo = Todo.objects.first()
        self.assertIsNone(todo.due_date)

    def test_create_todo_with_past_due_date(self):
        """Test that past dates can be set as due dates."""
        past_date = (timezone.now() - timedelta(days=5)).date()
        data = {'title': 'Past Task', 'due_date': past_date}
        response = self.client.post(self.create_url, data)

        todo = Todo.objects.first()
        self.assertEqual(todo.due_date, past_date)


class TodoEditViewTests(BaseTestCase):
    """Tests for editing todos."""

    def setUp(self):
        """Set up test data."""
        super().setUp()
        self.todo = create_todo(
            title="Original Title",
            description="Original Description"
        )
        self.edit_url = reverse('todo-edit', args=[self.todo.pk])
        self.list_url = reverse('todo-list')

    def test_edit_view_get_request(self):
        """Test GET request to edit view displays form."""
        response = self.client.get(self.edit_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'todos/todo_form.html')

    def test_edit_view_form_pre_filled(self):
        """Test that edit form is pre-filled with current data."""
        response = self.client.get(self.edit_url)
        form = response.context['form']

        self.assertEqual(form.instance.pk, self.todo.pk)
        self.assertEqual(form['title'].value(), 'Original Title')
        self.assertEqual(form['description'].value(), 'Original Description')

    def test_edit_todo_title(self):
        """Test updating only the title."""
        data = {
            'title': 'Updated Title',
            'description': 'Original Description'
        }
        response = self.client.post(self.edit_url, data)
        self.todo.refresh_from_db()
        self.assertEqual(self.todo.title, 'Updated Title')

    def test_edit_todo_description(self):
        """Test updating only the description."""
        data = {
            'title': 'Original Title',
            'description': 'Updated Description'
        }
        response = self.client.post(self.edit_url, data)
        self.todo.refresh_from_db()
        self.assertEqual(self.todo.description, 'Updated Description')

    def test_edit_todo_due_date(self):
        """Test updating the due date."""
        due_date = (timezone.now() + timedelta(days=10)).date()
        data = {'title': 'Original Title', 'due_date': due_date}
        response = self.client.post(self.edit_url, data)
        self.todo.refresh_from_db()
        self.assertEqual(self.todo.due_date, due_date)

    def test_edit_todo_redirects_to_list(self):
        """Test that after edit, user is redirected to list."""
        data = {'title': 'Updated Title'}
        response = self.client.post(self.edit_url, data, follow=False)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, self.list_url)

    def test_edit_nonexistent_todo(self):
        """Test editing a todo that doesn't exist."""
        nonexistent_url = reverse('todo-edit', args=[9999])
        response = self.client.get(nonexistent_url)
        self.assertEqual(response.status_code, 404)

    def test_edit_todo_without_changing_fields(self):
        """Test that submitting same data is idempotent."""
        data = {
            'title': 'Original Title',
            'description': 'Original Description'
        }
        response = self.client.post(self.edit_url, data)
        self.todo.refresh_from_db()

        self.assertEqual(self.todo.title, 'Original Title')
        self.assertEqual(self.todo.description, 'Original Description')


class TodoDeleteViewTests(BaseTestCase):
    """Tests for deleting todos."""

    def setUp(self):
        """Set up test data."""
        super().setUp()
        self.todo = create_todo(title="To Delete")
        self.delete_url = reverse('todo-delete', args=[self.todo.pk])
        self.list_url = reverse('todo-list')

    def test_delete_view_get_request(self):
        """Test GET request to delete view shows confirmation."""
        response = self.client.get(self.delete_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'todos/todo_confirm_delete.html')

    def test_delete_todo_post_request(self):
        """Test POST request deletes the todo."""
        response = self.client.post(self.delete_url)
        self.assertEqual(Todo.objects.count(), 0)

    def test_delete_todo_redirects_to_list(self):
        """Test redirect after deletion."""
        response = self.client.post(self.delete_url, follow=False)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, self.list_url)

    def test_delete_only_specific_todo(self):
        """Test that only the correct todo is deleted."""
        todo2 = create_todo(title="Keep This")
        response = self.client.post(self.delete_url)

        self.assertEqual(Todo.objects.count(), 1)
        self.assertEqual(Todo.objects.first().title, "Keep This")

    def test_delete_nonexistent_todo(self):
        """Test deleting a todo that doesn't exist."""
        nonexistent_url = reverse('todo-delete', args=[9999])
        response = self.client.get(nonexistent_url)
        self.assertEqual(response.status_code, 404)


class TodoResolveViewTests(BaseTestCase):
    """Tests for marking todos as resolved."""

    def setUp(self):
        """Set up test data."""
        super().setUp()
        self.todo = create_todo(title="Test Todo", resolved=False)
        self.resolve_url = reverse('todo-resolve', args=[self.todo.pk])
        self.list_url = reverse('todo-list')

    def test_resolve_todo_unresolved_to_resolved(self):
        """Test toggling from unresolved to resolved."""
        self.assertFalse(self.todo.resolved)
        response = self.client.post(self.resolve_url)

        self.todo.refresh_from_db()
        self.assertTrue(self.todo.resolved)

    def test_resolve_todo_resolved_to_unresolved(self):
        """Test toggling from resolved to unresolved."""
        self.todo.resolved = True
        self.todo.save()

        response = self.client.post(self.resolve_url)
        self.todo.refresh_from_db()
        self.assertFalse(self.todo.resolved)

    def test_resolve_todo_redirects_to_list(self):
        """Test that resolve redirects to list view."""
        response = self.client.post(self.resolve_url, follow=False)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, self.list_url)

    def test_resolve_only_affects_target_todo(self):
        """Test that resolving one todo doesn't affect others."""
        todo2 = create_todo(title="Other Todo", resolved=False)

        response = self.client.post(self.resolve_url)

        self.todo.refresh_from_db()
        todo2.refresh_from_db()
        self.assertTrue(self.todo.resolved)
        self.assertFalse(todo2.resolved)

    def test_resolve_nonexistent_todo(self):
        """Test resolving a todo that doesn't exist."""
        nonexistent_url = reverse('todo-resolve', args=[9999])
        response = self.client.post(nonexistent_url)
        self.assertEqual(response.status_code, 404)

    def test_resolve_idempotency(self):
        """Test that toggling multiple times works correctly."""
        # Unresolved -> Resolved
        self.client.post(self.resolve_url)
        self.todo.refresh_from_db()
        self.assertTrue(self.todo.resolved)

        # Resolved -> Unresolved
        self.client.post(self.resolve_url)
        self.todo.refresh_from_db()
        self.assertFalse(self.todo.resolved)

        # Unresolved -> Resolved again
        self.client.post(self.resolve_url)
        self.todo.refresh_from_db()
        self.assertTrue(self.todo.resolved)
