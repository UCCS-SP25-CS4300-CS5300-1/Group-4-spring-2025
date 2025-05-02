"""
This file contains the tests for the job filters.
"""

from django.test import SimpleTestCase
from home.templatetags.job_filters import format_field

class JobFiltersTests(SimpleTestCase):
    """
    This class contains the tests for the job filters.
    """

    def test_format_field_simple_underscore(self):
        """
        This function tests the format_field function with a simple underscore.
        """
        self.assertEqual(format_field('full_time'), 'Full Time')
        self.assertEqual(format_field('entry_level'), 'Entry Level')

    def test_format_field_simple_hyphen(self):
        """
        This function tests the format_field function with a simple hyphen.
        """
        self.assertEqual(format_field('part-time'), 'Part Time')

    def test_format_field_list_like_string_with_entity(self):
        """
        This function tests the format_field function with a list like string with an entity.
        """
        self.assertEqual(format_field('["Finance &amp; Accounting"]'), 'Finance & Accounting')

    def test_format_field_list_like_string_simple(self):
        """
        This function tests the format_field function with a list like string with a simple list.
        """
        self.assertEqual(format_field('["Sales"]'), 'Sales')
        self.assertEqual(format_field("['Marketing']"), 'Marketing') # Single quotes

    def test_format_field_string_with_entity(self):
        """
        This function tests the format_field function with a string with an entity.
        """
        self.assertEqual(format_field('Software &amp; IT'), 
                         'Software & It') # Note: title() behavior
        self.assertEqual(format_field('R&amp;D'), 'R&D') # title() keeps capitals after non-letter

    def test_format_field_empty_or_none(self):
        """
        This function tests the format_field function with an empty or none value.
        """
        self.assertEqual(format_field(''), '')
        self.assertIsNone(format_field(None))

    def test_format_field_non_string(self):
        """
        This function tests the format_field function with a non-string value.
        """
        self.assertEqual(format_field(123), 123)
        self.assertEqual(format_field(True), True)

    def test_format_field_list_input(self):
        """
        This function tests the format_field function with a list input.
        """
        self.assertEqual(format_field("['Item 1', 'Item 2']"), "Item 1")

    def test_format_field_html_escape(self):
        """
        This function tests the format_field function with an html escape.
        """
        self.assertEqual(format_field("Test &amp; Escape"), "Test & Escape")

    def test_format_field_already_formatted(self):
        """
        This function tests the format_field function with an already formatted value.
        """
        self.assertEqual(format_field('Already Formatted'), 'Already Formatted')

    def test_format_field_multiple_words(self):
        """
        This function tests the format_field function with multiple words.
        """
        self.assertEqual(format_field('senior_software_engineer'), 'Senior Software Engineer')
