"""
Tests for edge cases and special scenarios.

This module tests unusual situations, boundary conditions,
and business logic edge cases.
"""

from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta, date
from ..models import Todo
from .conftest import create_todo


class TodoBoundaryTests(TestCase):
    """Tests for boundary conditions and limits."""

    def test_create_todo_with_minimum_title(self):
        """Test creating todo with single character title."""
        todo = create_todo(title="A")
        self.assertEqual(todo.title, "A")

    def test_create_todo_with_maximum_title(self):
        """Test creating todo with maximum length title."""
        max_title = "A" * 200
        todo = create_todo(title=max_title)
        self.assertEqual(len(todo.title), 200)

    def test_create_todo_with_empty_description(self):
        """Test creating todo with completely empty description."""
        todo = create_todo(title="Test", description="")
        self.assertEqual(todo.description, "")

    def test_create_todo_with_very_large_description(self):
        """Test creating todo with very large description."""
        large_desc = "A" * 100000  # 100KB of text
        todo = create_todo(title="Test", description=large_desc)
        self.assertEqual(len(todo.description), 100000)

    def test_same_title_different_todos(self):
        """Test that multiple todos can have identical titles."""
        title = "Duplicate Task"
        todo1 = create_todo(title=title)
        todo2 = create_todo(title=title)

        self.assertEqual(todo1.title, todo2.title)
        self.assertNotEqual(todo1.pk, todo2.pk)

    def test_due_date_very_far_in_future(self):
        """Test due date far in the future."""
        far_future = date(year=2099, month=12, day=31)
        todo = create_todo(title="Future Task", due_date=far_future)
        self.assertEqual(todo.due_date, far_future)

    def test_due_date_very_far_in_past(self):
        """Test due date far in the past."""
        far_past = date(year=1970, month=1, day=1)
        todo = create_todo(title="Ancient Task", due_date=far_past)
        self.assertEqual(todo.due_date, far_past)


class TodoConcurrencyTests(TestCase):
    """Tests for concurrent operation scenarios."""

    def test_create_multiple_todos_same_second(self):
        """Test creating multiple todos rapidly."""
        todos = []
        for i in range(10):
            todo = create_todo(title=f"Task {i}")
            todos.append(todo)

        self.assertEqual(Todo.objects.count(), 10)
        # Verify all have different PKs
        pks = [t.pk for t in todos]
        self.assertEqual(len(set(pks)), 10)

    def test_update_and_delete_same_todo_sequence(self):
        """Test update followed by delete."""
        todo = create_todo(title="Original")
        todo_id = todo.pk

        # Update
        todo.title = "Updated"
        todo.save()

        # Verify update
        self.assertEqual(Todo.objects.get(pk=todo_id).title, "Updated")

        # Delete
        todo.delete()

        # Verify deletion
        self.assertEqual(Todo.objects.filter(pk=todo_id).count(), 0)


class TodoDataValidationTests(TestCase):
    """Tests for data validation and type handling."""

    def test_resolved_boolean_true(self):
        """Test resolved field properly stores True."""
        todo = create_todo(resolved=True)
        self.assertIs(todo.resolved, True)
        self.assertEqual(type(todo.resolved), bool)

    def test_resolved_boolean_false(self):
        """Test resolved field properly stores False."""
        todo = create_todo(resolved=False)
        self.assertIs(todo.resolved, False)
        self.assertEqual(type(todo.resolved), bool)

    def test_due_date_type_is_date(self):
        """Test that due_date is stored as date type."""
        test_date = date(2025, 12, 25)
        todo = create_todo(due_date=test_date)
        self.assertEqual(type(todo.due_date), date)

    def test_title_type_is_string(self):
        """Test that title is stored as string."""
        todo = create_todo(title="Test")
        self.assertEqual(type(todo.title), str)

    def test_created_at_is_datetime(self):
        """Test that created_at is datetime type."""
        todo = create_todo()
        from django.utils.timezone import datetime
        self.assertEqual(type(todo.created_at).__name__, 'datetime')

    def test_updated_at_is_datetime(self):
        """Test that updated_at is datetime type."""
        todo = create_todo()
        from django.utils.timezone import datetime
        self.assertEqual(type(todo.updated_at).__name__, 'datetime')


class TodoSpecialCharacterTests(TestCase):
    """Tests for handling special characters and encodings."""

    def test_unicode_characters_in_title(self):
        """Test unicode characters in title."""
        unicode_title = "Task: 中文 العربية Русский Ελληνικά"
        todo = create_todo(title=unicode_title)
        self.assertEqual(todo.title, unicode_title)

    def test_emoji_in_description(self):
        """Test emoji characters in description."""
        emoji_desc = "🎯 📝 ✓ 🚀 Done!"
        todo = create_todo(description=emoji_desc)
        self.assertEqual(todo.description, emoji_desc)

    def test_sql_injection_attempt_in_title(self):
        """Test that SQL injection attempts are safely handled."""
        malicious_title = "'; DROP TABLE todos; --"
        todo = create_todo(title=malicious_title)
        self.assertEqual(todo.title, malicious_title)
        # Verify table still exists
        self.assertGreaterEqual(Todo.objects.count(), 1)

    def test_html_tags_in_description(self):
        """Test that HTML tags are stored as text, not rendered."""
        html_content = "<script>alert('xss')</script><b>Bold</b>"
        todo = create_todo(description=html_content)
        self.assertEqual(todo.description, html_content)

    def test_newlines_in_description(self):
        """Test that newlines are preserved in description."""
        multiline = "Line 1\nLine 2\r\nLine 3"
        todo = create_todo(description=multiline)
        self.assertEqual(todo.description, multiline)

    def test_tabs_and_spaces_in_description(self):
        """Test that whitespace variations are preserved."""
        whitespace_text = "Text with\ttabs\t and   spaces   "
        todo = create_todo(description=whitespace_text)
        self.assertEqual(todo.description, whitespace_text)

    def test_null_bytes_in_title(self):
        """Test handling of null bytes."""
        # Most frameworks reject null bytes
        try:
            title_with_null = "Task\x00Name"
            todo = create_todo(title=title_with_null)
            # If it gets created, verify it's stored
            self.assertIn("\x00", todo.title)
        except (ValueError, TypeError):
            # Null bytes should be rejected
            pass


class TodoStateTransitionTests(TestCase):
    """Tests for state transitions and workflows."""

    def test_resolve_unresolved_todo(self):
        """Test changing resolved from False to True."""
        todo = create_todo(resolved=False)
        self.assertFalse(todo.resolved)
        todo.resolved = True
        todo.save()
        self.assertTrue(todo.resolved)

    def test_unresolve_resolved_todo(self):
        """Test changing resolved from True to False."""
        todo = create_todo(resolved=True)
        self.assertTrue(todo.resolved)
        todo.resolved = False
        todo.save()
        self.assertFalse(todo.resolved)

    def test_toggle_resolved_multiple_times(self):
        """Test toggling resolved status multiple times."""
        todo = create_todo(resolved=False)

        for i in range(10):
            todo.resolved = not todo.resolved
            todo.save()
            # After i+1 toggles, resolved should be True for odd numbers, False for even
            expected_resolved = (i + 1) % 2 == 1
            self.assertEqual(todo.resolved, expected_resolved)

    def test_update_without_changing_resolved(self):
        """Test that updating other fields doesn't change resolved."""
        todo = create_todo(title="Original", resolved=False)
        todo.title = "Updated"
        todo.save()
        self.assertFalse(todo.resolved)

    def test_change_due_date_on_resolved_todo(self):
        """Test changing due date on already resolved todo."""
        old_date = date(2025, 1, 1)
        new_date = date(2025, 12, 31)
        todo = create_todo(due_date=old_date, resolved=True)

        todo.due_date = new_date
        todo.save()

        self.assertEqual(todo.due_date, new_date)
        self.assertTrue(todo.resolved)


class TodoListFilteringTests(TestCase):
    """Tests for list filtering and querying scenarios."""

    def test_count_resolved_todos(self):
        """Test that we can count resolved todos."""
        create_todo(title="Task 1", resolved=True)
        create_todo(title="Task 2", resolved=False)
        create_todo(title="Task 3", resolved=True)

        resolved_count = Todo.objects.filter(resolved=True).count()
        self.assertEqual(resolved_count, 2)

    def test_count_unresolved_todos(self):
        """Test that we can count unresolved todos."""
        create_todo(title="Task 1", resolved=True)
        create_todo(title="Task 2", resolved=False)
        create_todo(title="Task 3", resolved=False)

        unresolved_count = Todo.objects.filter(resolved=False).count()
        self.assertEqual(unresolved_count, 2)

    def test_filter_todos_by_due_date(self):
        """Test filtering todos by due date."""
        soon_date = (timezone.now() + timedelta(days=3)).date()
        create_todo(title="Soon", due_date=soon_date)
        create_todo(title="Later", due_date=(timezone.now() + timedelta(days=10)).date())

        soon_todos = Todo.objects.filter(due_date=soon_date)
        self.assertEqual(soon_todos.count(), 1)

    def test_filter_todos_without_due_date(self):
        """Test filtering todos that have no due date."""
        create_todo(title="No Date", due_date=None)
        create_todo(title="Has Date", due_date=date(2025, 12, 25))

        no_date_todos = Todo.objects.filter(due_date__isnull=True)
        self.assertEqual(no_date_todos.count(), 1)

    def test_todos_with_upcoming_due_dates(self):
        """Test finding todos with due dates in next 7 days."""
        now = timezone.now().date()

        create_todo(title="Today", due_date=now)
        create_todo(title="Tomorrow", due_date=now + timedelta(days=1))
        create_todo(title="Next Week", due_date=now + timedelta(days=7))
        create_todo(title="Far Future", due_date=now + timedelta(days=30))

        upcoming = Todo.objects.filter(
            due_date__gte=now,
            due_date__lte=now + timedelta(days=7)
        )
        self.assertEqual(upcoming.count(), 3)


class TodoQueryPerformanceTests(TestCase):
    """Tests for basic query patterns and scenarios."""

    def test_bulk_todo_creation(self):
        """Test creating many todos efficiently."""
        todos = [create_todo(title=f"Task {i}") for i in range(100)]
        self.assertEqual(Todo.objects.count(), 100)

    def test_retrieve_all_todos(self):
        """Test retrieving all todos."""
        for i in range(50):
            create_todo(title=f"Task {i}")

        all_todos = Todo.objects.all()
        self.assertEqual(all_todos.count(), 50)

    def test_update_all_todos_resolved_status(self):
        """Test bulk update of todos."""
        for i in range(20):
            create_todo(title=f"Task {i}", resolved=False)

        Todo.objects.all().update(resolved=True)
        resolved_count = Todo.objects.filter(resolved=True).count()
        self.assertEqual(resolved_count, 20)
