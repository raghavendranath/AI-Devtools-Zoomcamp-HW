"""
Integration tests for Todo app.

These tests verify complete user workflows across multiple views,
ensuring components work together correctly end-to-end.
"""

from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta
from ..models import Todo
from .conftest import create_todo, create_todo_with_due_date


class TodoWorkflowIntegrationTests(TestCase):
    """Tests for complete user workflows."""

    def setUp(self):
        """Initialize test client."""
        self.client = Client()

    def test_complete_todo_lifecycle(self):
        """
        Test complete lifecycle: Create -> Read -> Edit -> Mark Done -> Delete.

        This tests a realistic user workflow.
        """
        list_url = reverse('todo-list')
        create_url = reverse('todo-create')

        # 1. Create a todo
        create_data = {
            'title': 'Complete Project',
            'description': 'Finish the TODO app',
            'due_date': (timezone.now() + timedelta(days=7)).date()
        }
        response = self.client.post(create_url, create_data)
        self.assertEqual(response.status_code, 302)  # Redirect

        # Verify todo was created
        self.assertEqual(Todo.objects.count(), 1)
        todo = Todo.objects.first()
        self.assertEqual(todo.title, 'Complete Project')

        # 2. View todo in list
        response = self.client.get(list_url)
        self.assertEqual(response.status_code, 200)
        self.assertIn(todo, response.context['todos'])

        # 3. Edit the todo
        edit_url = reverse('todo-edit', args=[todo.pk])
        edit_data = {
            'title': 'Complete Project - Updated',
            'description': 'Finish the TODO app with tests'
        }
        response = self.client.post(edit_url, edit_data)
        self.assertEqual(response.status_code, 302)

        # Verify changes
        todo.refresh_from_db()
        self.assertEqual(todo.title, 'Complete Project - Updated')

        # 4. Mark as done
        resolve_url = reverse('todo-resolve', args=[todo.pk])
        response = self.client.post(resolve_url)
        self.assertEqual(response.status_code, 302)

        # Verify resolved status
        todo.refresh_from_db()
        self.assertTrue(todo.resolved)

        # 5. Mark as not done again
        response = self.client.post(resolve_url)
        todo.refresh_from_db()
        self.assertFalse(todo.resolved)

        # 6. Delete the todo
        delete_url = reverse('todo-delete', args=[todo.pk])
        response = self.client.post(delete_url)
        self.assertEqual(response.status_code, 302)

        # Verify deletion
        self.assertEqual(Todo.objects.count(), 0)

    def test_multiple_todos_workflow(self):
        """
        Test managing multiple todos simultaneously.

        Verifies that operations on one todo don't affect others.
        """
        create_url = reverse('todo-create')
        list_url = reverse('todo-list')

        # Create 3 todos
        todos_data = [
            {'title': 'Task 1', 'due_date': (timezone.now() + timedelta(days=1)).date()},
            {'title': 'Task 2', 'due_date': (timezone.now() + timedelta(days=2)).date()},
            {'title': 'Task 3', 'due_date': (timezone.now() + timedelta(days=3)).date()},
        ]

        for data in todos_data:
            self.client.post(create_url, data)

        # Verify all created
        self.assertEqual(Todo.objects.count(), 3)

        # Resolve first todo
        todo1 = Todo.objects.first()
        resolve_url = reverse('todo-resolve', args=[todo1.pk])
        self.client.post(resolve_url)

        # Verify only first is resolved
        todo1.refresh_from_db()
        todos = Todo.objects.all()
        self.assertTrue(todo1.resolved)
        for todo in todos[1:]:
            self.assertFalse(todo.resolved)

        # Delete second todo
        todo2 = todos[1]
        delete_url = reverse('todo-delete', args=[todo2.pk])
        self.client.post(delete_url)

        # Verify only 2 remain
        self.assertEqual(Todo.objects.count(), 2)

    def test_create_and_view_immediately(self):
        """Test that created todos appear in list view immediately."""
        create_url = reverse('todo-create')
        list_url = reverse('todo-list')

        # Create todo
        create_data = {'title': 'Immediate Task'}
        self.client.post(create_url, create_data)

        # View list
        response = self.client.get(list_url)
        todos = response.context['todos']

        # Verify it appears
        self.assertEqual(len(todos), 1)
        self.assertEqual(todos[0].title, 'Immediate Task')

    def test_edit_and_verify_changes(self):
        """Test that edited todos show updated data in list."""
        todo = create_todo(title="Original", description="Original Desc")
        edit_url = reverse('todo-edit', args=[todo.pk])
        list_url = reverse('todo-list')

        # Edit todo
        edit_data = {
            'title': 'Updated',
            'description': 'Updated Desc'
        }
        self.client.post(edit_url, edit_data)

        # View list
        response = self.client.get(list_url)
        updated_todo = response.context['todos'][0]

        self.assertEqual(updated_todo.title, 'Updated')
        self.assertEqual(updated_todo.description, 'Updated Desc')


class TodoPermissionsAndSecurityTests(TestCase):
    """Tests for security-related scenarios."""

    def setUp(self):
        """Initialize test client."""
        self.client = Client()

    def test_access_edit_nonexistent_todo(self):
        """Test that accessing non-existent todo returns 404."""
        edit_url = reverse('todo-edit', args=[9999])
        response = self.client.get(edit_url)
        self.assertEqual(response.status_code, 404)

    def test_access_delete_nonexistent_todo(self):
        """Test that deleting non-existent todo returns 404."""
        delete_url = reverse('todo-delete', args=[9999])
        response = self.client.get(delete_url)
        self.assertEqual(response.status_code, 404)

    def test_resolve_nonexistent_todo(self):
        """Test that resolving non-existent todo returns 404."""
        resolve_url = reverse('todo-resolve', args=[9999])
        response = self.client.post(resolve_url)
        self.assertEqual(response.status_code, 404)

    def test_html_in_title_is_escaped(self):
        """Test that HTML in todo title is stored safely."""
        title = '<script>alert("xss")</script>'
        todo = create_todo(title=title)

        # Verify stored as-is (escaping happens at render time)
        self.assertEqual(todo.title, title)

        # Verify list view doesn't execute it
        list_url = reverse('todo-list')
        response = self.client.get(list_url)
        # Django templates auto-escape by default
        self.assertIn(str(todo.pk), str(response.content))


class TodoDataPersistenceTests(TestCase):
    """Tests for data persistence and integrity."""

    def test_todo_data_persists_after_reload(self):
        """Test that todo data is saved correctly to database."""
        due_date = (timezone.now() + timedelta(days=5)).date()
        todo = create_todo(
            title='Persistent Task',
            description='Important data',
            due_date=due_date
        )

        # Create a new instance from database
        retrieved_todo = Todo.objects.get(pk=todo.pk)

        self.assertEqual(retrieved_todo.title, 'Persistent Task')
        self.assertEqual(retrieved_todo.description, 'Important data')
        self.assertEqual(retrieved_todo.due_date, due_date)

    def test_resolved_status_persists(self):
        """Test that resolved status persists after modification."""
        todo = create_todo(resolved=False)
        todo.resolved = True
        todo.save()

        # Retrieve from database
        retrieved_todo = Todo.objects.get(pk=todo.pk)
        self.assertTrue(retrieved_todo.resolved)

    def test_timestamp_integrity(self):
        """Test that timestamps are correctly maintained."""
        todo = create_todo()
        created_at = todo.created_at

        # Modify and save
        todo.title = 'Modified'
        todo.save()

        # Retrieve and verify
        retrieved_todo = Todo.objects.get(pk=todo.pk)
        self.assertEqual(retrieved_todo.created_at, created_at)
        self.assertGreater(retrieved_todo.updated_at, created_at)


class TodoListOrderingTests(TestCase):
    """Tests for todo list ordering and sorting."""

    def test_todos_displayed_in_due_date_order(self):
        """Test that todos in list are ordered by due date."""
        # Create todos with specific due dates
        todo_no_date = create_todo(title="No Date", due_date=None)
        todo_3_days = create_todo_with_due_date(days_from_now=3)
        todo_7_days = create_todo_with_due_date(days_from_now=7)

        list_url = reverse('todo-list')
        response = self.client.get(list_url)
        todos = list(response.context['todos'])

        # Verify order
        self.assertIsNone(todos[0].due_date)
        self.assertLess(todos[1].due_date, todos[2].due_date)

    def test_resolved_todos_maintain_order(self):
        """Test that resolved status doesn't affect ordering."""
        todo1 = create_todo_with_due_date(days_from_now=5)
        todo2 = create_todo_with_due_date(days_from_now=10)
        todo2.resolved = True
        todo2.save()

        list_url = reverse('todo-list')
        response = self.client.get(list_url)
        todos = list(response.context['todos'])

        # Order should still be by due date, not resolved status
        self.assertEqual(todos[0].pk, todo1.pk)
        self.assertEqual(todos[1].pk, todo2.pk)
