from django.test import SimpleTestCase
from home.templatetags.job_filters import format_field

class JobFiltersTests(SimpleTestCase):

    def test_format_field_simple_underscore(self):
        self.assertEqual(format_field('full_time'), 'Full Time')
        self.assertEqual(format_field('entry_level'), 'Entry Level')

    def test_format_field_simple_hyphen(self):
        self.assertEqual(format_field('part-time'), 'Part Time')

    def test_format_field_list_like_string_with_entity(self):
        self.assertEqual(format_field('["Finance &amp; Accounting"]'), 'Finance & Accounting')

    def test_format_field_list_like_string_simple(self):
        self.assertEqual(format_field('["Sales"]'), 'Sales')
        self.assertEqual(format_field("['Marketing']"), 'Marketing')

    def test_format_field_string_with_entity(self):
        self.assertEqual(format_field('Software &amp; IT'), 'Software & It')
        self.assertEqual(format_field('R&amp;D'), 'R&D')

    def test_format_field_empty_or_none(self):
        self.assertEqual(format_field(''), '')
        self.assertEqual(format_field(None), '')

    def test_format_field_non_string(self):
        self.assertEqual(format_field(123), 123)
        self.assertEqual(format_field(True), True)
        self.assertEqual(format_field([1, 2]), [1, 2])

    def test_format_field_malformed_list(self):
        self.assertEqual(format_field('["malformed_entity &amp; stuff'), 'Malformed Entity & Stuff')
        self.assertEqual(format_field('[Malformed Example]'), 'Malformed Example')
        self.assertEqual(format_field('Just Text'), 'Just Text')
        self.assertEqual(format_field('["[Double-Quoted]"]'), '[Double Quoted]')

    def test_format_field_already_formatted(self):
        self.assertEqual(format_field('Already Formatted'), 'Already Formatted')

    def test_format_field_multiple_words(self):
        self.assertEqual(format_field('senior_software_engineer'), 'Senior Software Engineer')