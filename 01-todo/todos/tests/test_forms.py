"""
Tests for Todo forms.

This module tests form validation, field constraints, and user input handling.
"""

from django.test import TestCase
from django.utils import timezone
from datetime import timedelta
from ..forms import TodoForm
from .conftest import BaseTestCase


class TodoFormValidationTests(BaseTestCase):
    """Tests for TodoForm validation."""

    def test_valid_form_with_all_fields(self):
        """Test form validation with all valid fields."""
        due_date = (timezone.now() + timedelta(days=5)).date()
        form = TodoForm(data={
            'title': 'Test Todo',
            'description': 'Test Description',
            'due_date': due_date
        })
        self.assertTrue(form.is_valid())

    def test_valid_form_with_required_field_only(self):
        """Test form validation with only required field."""
        form = TodoForm(data={'title': 'Test Todo'})
        self.assertTrue(form.is_valid())

    def test_form_missing_required_title(self):
        """Test form validation fails without title."""
        form = TodoForm(data={'description': 'No title provided'})
        self.assertFalse(form.is_valid())
        self.assertIn('title', form.errors)

    def test_form_title_field_required(self):
        """Test that title field is required."""
        form = TodoForm(data={})
        self.assertFalse(form.is_valid())
        self.assertIn('This field is required.', form.errors['title'])

    def test_form_accepts_empty_description(self):
        """Test form accepts empty description (optional field)."""
        form = TodoForm(data={
            'title': 'Test Todo',
            'description': ''
        })
        self.assertTrue(form.is_valid())

    def test_form_accepts_none_description(self):
        """Test form accepts None for description."""
        form = TodoForm(data={
            'title': 'Test Todo',
            'description': None
        })
        self.assertTrue(form.is_valid())

    def test_form_accepts_empty_due_date(self):
        """Test form accepts empty due date (optional field)."""
        form = TodoForm(data={
            'title': 'Test Todo',
            'due_date': ''
        })
        self.assertTrue(form.is_valid())

    def test_form_accepts_none_due_date(self):
        """Test form accepts None for due date."""
        form = TodoForm(data={
            'title': 'Test Todo',
            'due_date': None
        })
        self.assertTrue(form.is_valid())


class TodoFormFieldTests(TestCase):
    """Tests for individual form fields."""

    def test_form_title_field_max_length(self):
        """Test title field respects max_length."""
        long_title = "A" * 200  # Max length
        form = TodoForm(data={
            'title': long_title,
            'description': 'Valid description'
        })
        self.assertTrue(form.is_valid())

    def test_form_title_exceeds_max_length(self):
        """Test title field rejects too long titles."""
        long_title = "A" * 201  # Over max length
        form = TodoForm(data={
            'title': long_title,
            'description': 'Valid description'
        })
        self.assertFalse(form.is_valid())

    def test_form_description_can_be_very_long(self):
        """Test that description accepts large text."""
        long_description = "A" * 10000  # Very long description
        form = TodoForm(data={
            'title': 'Test Todo',
            'description': long_description
        })
        self.assertTrue(form.is_valid())

    def test_form_accepts_past_due_date(self):
        """Test form accepts past dates as due dates."""
        past_date = (timezone.now() - timedelta(days=5)).date()
        form = TodoForm(data={
            'title': 'Test Todo',
            'due_date': past_date
        })
        self.assertTrue(form.is_valid())

    def test_form_accepts_future_due_date(self):
        """Test form accepts future dates as due dates."""
        future_date = (timezone.now() + timedelta(days=30)).date()
        form = TodoForm(data={
            'title': 'Test Todo',
            'due_date': future_date
        })
        self.assertTrue(form.is_valid())

    def test_form_accepts_today_as_due_date(self):
        """Test form accepts today's date as due date."""
        today = timezone.now().date()
        form = TodoForm(data={
            'title': 'Test Todo',
            'due_date': today
        })
        self.assertTrue(form.is_valid())


class TodoFormFieldWidgetsTests(TestCase):
    """Tests for form field widgets and CSS classes."""

    def test_form_has_bootstrap_classes(self):
        """Test that form fields have Bootstrap CSS classes."""
        form = TodoForm()
        self.assertIn('form-control', str(form['title']))
        self.assertIn('form-control', str(form['description']))
        self.assertIn('form-control', str(form['due_date']))

    def test_title_field_has_placeholder(self):
        """Test that title field has placeholder."""
        form = TodoForm()
        self.assertIn('placeholder', str(form['title']))
        self.assertIn('Enter task title', str(form['title']))

    def test_description_field_has_placeholder(self):
        """Test that description field has placeholder."""
        form = TodoForm()
        self.assertIn('placeholder', str(form['description']))
        self.assertIn('Enter task description', str(form['description']))

    def test_description_field_has_rows_attribute(self):
        """Test that description field has rows attribute."""
        form = TodoForm()
        self.assertIn('rows', str(form['description']))

    def test_due_date_field_is_date_input(self):
        """Test that due_date field uses date input type."""
        form = TodoForm()
        self.assertIn('type="date"', str(form['due_date']))


class TodoFormSpecialCharactersTests(TestCase):
    """Tests for handling special characters and XSS prevention."""

    def test_form_accepts_special_characters_in_title(self):
        """Test form accepts special characters in title."""
        special_title = "Task with <script>alert('xss')</script>"
        form = TodoForm(data={
            'title': special_title,
            'description': 'Valid'
        })
        self.assertTrue(form.is_valid())

    def test_form_accepts_special_characters_in_description(self):
        """Test form accepts special characters in description."""
        special_desc = "<script>alert('xss')</script>"
        form = TodoForm(data={
            'title': 'Test Todo',
            'description': special_desc
        })
        self.assertTrue(form.is_valid())

    def test_form_accepts_emoji_in_title(self):
        """Test form accepts emoji characters."""
        emoji_title = "Task 🎯 with emoji 😊"
        form = TodoForm(data={
            'title': emoji_title,
            'description': 'Valid'
        })
        self.assertTrue(form.is_valid())

    def test_form_accepts_multiline_description(self):
        """Test form accepts newlines in description."""
        multiline_desc = "Line 1\nLine 2\nLine 3"
        form = TodoForm(data={
            'title': 'Test Todo',
            'description': multiline_desc
        })
        self.assertTrue(form.is_valid())

    def test_form_accepts_html_in_description(self):
        """Test form accepts HTML-like content (for storing, not rendering)."""
        html_desc = "<div>Some HTML</div>"
        form = TodoForm(data={
            'title': 'Test Todo',
            'description': html_desc
        })
        self.assertTrue(form.is_valid())


class TodoFormEdgeCasesTests(TestCase):
    """Tests for edge cases and boundary conditions."""

    def test_form_with_whitespace_only_title(self):
        """Test form with whitespace-only title."""
        form = TodoForm(data={
            'title': '   ',
            'description': 'Valid'
        })
        # Django's CharField strips whitespace by default, so whitespace-only is treated as empty
        self.assertFalse(form.is_valid())

    def test_form_with_whitespace_description(self):
        """Test form with whitespace-only description."""
        form = TodoForm(data={
            'title': 'Test Todo',
            'description': '   \n  \t  '
        })
        self.assertTrue(form.is_valid())

    def test_form_with_unicode_characters(self):
        """Test form accepts unicode characters."""
        unicode_title = "任务 مهمة Задача"
        form = TodoForm(data={
            'title': unicode_title,
            'description': 'Valid'
        })
        self.assertTrue(form.is_valid())

    def test_form_preserves_whitespace_in_description(self):
        """Test that form preserves spacing in description."""
        desc_with_spaces = "Task with    multiple     spaces"
        form = TodoForm(data={
            'title': 'Test',
            'description': desc_with_spaces
        })
        self.assertTrue(form.is_valid())
        # Whitespace is preserved in the cleaned_data
        self.assertEqual(form.cleaned_data['description'], desc_with_spaces)

    def test_form_date_string_parsing(self):
        """Test that form correctly parses date strings."""
        form = TodoForm(data={
            'title': 'Test Todo',
            'due_date': '2025-12-25'
        })
        self.assertTrue(form.is_valid())

    def test_form_invalid_date_format(self):
        """Test form rejects invalid date formats."""
        form = TodoForm(data={
            'title': 'Test Todo',
            'due_date': 'invalid-date'
        })
        self.assertFalse(form.is_valid())
        self.assertIn('due_date', form.errors)
