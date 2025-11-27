"""
Shared test configuration and fixtures.

This module provides reusable fixtures, setup, and utility functions
used across multiple test modules to follow DRY principles.
"""

from django.test import Client
from django.utils import timezone
from datetime import timedelta
from django.test import TestCase
from ..models import Todo


def create_todo(
    title="Default Todo",
    description=None,
    due_date=None,
    resolved=False
):
    """
    Factory function to create a Todo instance for testing.

    This helps maintain DRY principle by centralizing test data creation.

    Args:
        title (str): Todo title
        description (str, optional): Todo description
        due_date (date, optional): Due date for the todo
        resolved (bool): Whether todo is resolved

    Returns:
        Todo: Created todo instance
    """
    return Todo.objects.create(
        title=title,
        description=description,
        due_date=due_date,
        resolved=resolved
    )


def create_todo_with_due_date(days_from_now=5):
    """
    Create a todo with a due date N days from now.

    Args:
        days_from_now (int): Number of days from today for due date

    Returns:
        Todo: Created todo instance with due date
    """
    due_date = (timezone.now() + timedelta(days=days_from_now)).date()
    return create_todo(
        title=f"Todo due in {days_from_now} days",
        due_date=due_date
    )


class BaseTestCase(TestCase):
    """
    Base test case class that provides common setup for all test classes.

    This follows the DRY principle by centralizing common test setup.
    """

    def setUp(self):
        """Initialize test client and common test data."""
        self.client = Client()
        self.now = timezone.now()

    def assert_redirect_to_list(self, response, follow=False):
        """
        Assert that response redirects to todo list.

        Args:
            response: HTTP response object
            follow (bool): Whether to follow redirects
        """
        from django.urls import reverse
        if not follow:
            self.assertEqual(response.status_code, 302)
            self.assertEqual(response.url, reverse('todo-list'))
        else:
            self.assertEqual(response.status_code, 200)
