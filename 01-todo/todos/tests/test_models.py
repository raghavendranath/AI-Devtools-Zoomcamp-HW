"""
Tests for the Todo model.

This module tests the data layer, ensuring the model correctly
stores and retrieves data with proper validation and defaults.
"""

from django.test import TestCase
from django.utils import timezone
from datetime import timedelta
from ..models import Todo
from .conftest import create_todo, create_todo_with_due_date


class TodoModelCreationTests(TestCase):
    """Tests for creating Todo instances."""

    def test_create_todo_with_required_fields_only(self):
        """Test creating a todo with only the required field (title)."""
        todo = create_todo(title="Simple Task")

        self.assertEqual(todo.title, "Simple Task")
        self.assertIsNone(todo.description)
        self.assertIsNone(todo.due_date)
        self.assertFalse(todo.resolved)
        self.assertEqual(Todo.objects.count(), 1)

    def test_create_todo_with_all_fields(self):
        """Test creating a todo with all fields including optional ones."""
        due_date = timezone.now().date() + timedelta(days=7)
        todo = create_todo(
            title="Complete Task",
            description="Full description",
            due_date=due_date,
            resolved=False
        )

        self.assertEqual(todo.title, "Complete Task")
        self.assertEqual(todo.description, "Full description")
        self.assertEqual(todo.due_date, due_date)
        self.assertFalse(todo.resolved)

    def test_default_resolved_is_false(self):
        """Test that new todos are not resolved by default."""
        todo = create_todo()
        self.assertFalse(todo.resolved)

    def test_title_max_length_validation(self):
        """Test that title respects max_length constraint."""
        long_title = "A" * 200  # Max length
        todo = create_todo(title=long_title)
        self.assertEqual(len(todo.title), 200)

    def test_title_cannot_exceed_max_length(self):
        """Test that title exceeding max_length fails."""
        long_title = "A" * 201  # Over max length
        with self.assertRaises(Exception):
            create_todo(title=long_title)
            todo = Todo.objects.get(title__startswith="A")
            # Force full_clean to validate
            todo.full_clean()


class TodoModelFieldsTests(TestCase):
    """Tests for Todo model fields and their behavior."""

    def test_timestamps_are_set_on_creation(self):
        """Test that created_at and updated_at are automatically set."""
        before = timezone.now()
        todo = create_todo(title="Test Todo")
        after = timezone.now()

        self.assertIsNotNone(todo.created_at)
        self.assertIsNotNone(todo.updated_at)
        self.assertTrue(before <= todo.created_at <= after)
        self.assertTrue(before <= todo.updated_at <= after)

    def test_updated_at_changes_on_modification(self):
        """Test that updated_at updates when todo is modified."""
        todo = create_todo(title="Original Title")
        original_updated_at = todo.updated_at

        # Wait a moment and update
        import time
        time.sleep(0.01)

        todo.title = "Updated Title"
        todo.save()

        self.assertNotEqual(todo.updated_at, original_updated_at)
        self.assertGreater(todo.updated_at, original_updated_at)

    def test_created_at_does_not_change_on_update(self):
        """Test that created_at remains unchanged when todo is modified."""
        todo = create_todo(title="Original Title")
        original_created_at = todo.created_at

        todo.title = "Updated Title"
        todo.save()

        self.assertEqual(todo.created_at, original_created_at)

    def test_description_can_be_null(self):
        """Test that description field accepts null values."""
        todo = create_todo(title="No Description", description=None)
        self.assertIsNone(todo.description)

    def test_description_can_be_empty_string(self):
        """Test that description field accepts empty strings."""
        todo = create_todo(title="Empty Description", description="")
        self.assertEqual(todo.description, "")

    def test_due_date_can_be_null(self):
        """Test that due_date field accepts null values."""
        todo = create_todo(title="No Due Date", due_date=None)
        self.assertIsNone(todo.due_date)

    def test_past_due_dates_are_allowed(self):
        """Test that past dates can be set as due dates."""
        past_date = (timezone.now() - timedelta(days=10)).date()
        todo = create_todo(title="Past Due", due_date=past_date)
        self.assertEqual(todo.due_date, past_date)

    def test_future_due_dates_are_allowed(self):
        """Test that future dates can be set as due dates."""
        future_date = (timezone.now() + timedelta(days=30)).date()
        todo = create_todo(title="Future Due", due_date=future_date)
        self.assertEqual(todo.due_date, future_date)


class TodoModelStringRepresentationTests(TestCase):
    """Tests for model string representation."""

    def test_todo_string_representation(self):
        """Test the __str__ method returns the title."""
        todo = create_todo(title="My Todo Title")
        self.assertEqual(str(todo), "My Todo Title")

    def test_todo_string_representation_with_special_characters(self):
        """Test __str__ with special characters."""
        title = "Todo with 🎯 emoji & special chars!"
        todo = create_todo(title=title)
        self.assertEqual(str(todo), title)


class TodoModelResolvedStatusTests(TestCase):
    """Tests for the resolved status functionality."""

    def test_resolved_toggle_true_to_false(self):
        """Test toggling resolved status from True to False."""
        todo = create_todo(title="Test Todo", resolved=True)
        self.assertTrue(todo.resolved)

        todo.resolved = False
        todo.save()
        self.assertFalse(todo.resolved)

    def test_resolved_toggle_false_to_true(self):
        """Test toggling resolved status from False to True."""
        todo = create_todo(title="Test Todo", resolved=False)
        self.assertFalse(todo.resolved)

        todo.resolved = True
        todo.save()
        self.assertTrue(todo.resolved)

    def test_multiple_todos_have_independent_resolved_status(self):
        """Test that resolved status is independent for each todo."""
        todo1 = create_todo(title="Todo 1", resolved=True)
        todo2 = create_todo(title="Todo 2", resolved=False)

        self.assertTrue(todo1.resolved)
        self.assertFalse(todo2.resolved)


class TodoModelOrderingTests(TestCase):
    """Tests for model ordering and default querysets."""

    def test_todos_ordered_by_due_date(self):
        """Test that todos are ordered by due_date by default."""
        # Create todos with specific due dates in random order
        todo_no_date = create_todo(title="No Date", due_date=None)
        todo_future = create_todo_with_due_date(days_from_now=30)
        todo_soon = create_todo_with_due_date(days_from_now=5)

        todos = Todo.objects.all()

        # Todos without due_date come first (NULL values sort first in most databases)
        self.assertIsNone(todos[0].due_date)
        # Then ordered by due_date ascending
        self.assertLess(todos[1].due_date, todos[2].due_date)

    def test_multiple_todos_same_due_date(self):
        """Test handling of multiple todos with the same due date."""
        due_date = (timezone.now() + timedelta(days=5)).date()
        todo1 = create_todo(title="Task 1", due_date=due_date)
        todo2 = create_todo(title="Task 2", due_date=due_date)

        todos = list(Todo.objects.filter(due_date=due_date))
        self.assertEqual(len(todos), 2)
        self.assertEqual(todos[0].due_date, todos[1].due_date)


class TodoModelTitleUniquenessTests(TestCase):
    """Tests for title uniqueness (or lack thereof)."""

    def test_duplicate_titles_are_allowed(self):
        """Test that multiple todos can have the same title."""
        create_todo(title="Duplicate Task")
        create_todo(title="Duplicate Task")

        self.assertEqual(Todo.objects.filter(title="Duplicate Task").count(), 2)

    def test_long_description_handling(self):
        """Test that very long descriptions are handled correctly."""
        long_description = "A" * 5000
        todo = create_todo(title="Long Description", description=long_description)
        self.assertEqual(len(todo.description), 5000)
