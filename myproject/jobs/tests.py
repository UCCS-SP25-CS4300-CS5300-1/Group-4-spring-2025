from django.test import TestCase, Client
from django.urls import reverse
from .models import Job

class JobSearchTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.job1 = Job.objects.create(
            title="Software Engineer",
            industry="Technology",
            location="Denver",
            is_remote=True,
            salary_min=50000,
            salary_max=80000
        )
        self.job2 = Job.objects.create(
            title="Marketing Specialist",
            industry="Marketing",
            location="New York",
            is_remote=False,
            salary_min=40000,
            salary_max=60000
        )
        self.job3 = Job.objects.create(
            title="Remote Developer",
            industry="Technology",
            location="Remote",
            is_remote=True,
            salary_min=70000,
            salary_max=100000
        )

    def test_search_by_industry(self):
        url = reverse('search_jobs')
        response = self.client.get(url, {'industry': 'Technology'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Software Engineer")
        self.assertContains(response, "Remote Developer")
        self.assertNotContains(response, "Marketing Specialist")

    def test_search_by_location(self):
        url = reverse('search_jobs')
        response = self.client.get(url, {'location': 'Denver'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Software Engineer")
        self.assertNotContains(response, "Marketing Specialist")
        self.assertNotContains(response, "Remote Developer")

    def test_search_by_remote(self):
        url = reverse('search_jobs')
        response = self.client.get(url, {'remote': 'yes'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Software Engineer")
        self.assertContains(response, "Remote Developer")
        self.assertNotContains(response, "Marketing Specialist")

    def test_search_by_salary_range(self):
        url = reverse('search_jobs')
        response = self.client.get(url, {'salary_min': '60000', 'salary_max': '90000'})
        self.assertEqual(response.status_code, 200)

        self.assertNotContains(response, "Software Engineer")

        self.assertNotContains(response, "Marketing Specialist")

        self.assertContains(response, "Remote Developer")

    def test_search_by_salary_min_only(self):
        url = reverse('search_jobs')
        response = self.client.get(url, {'salary_min': '45000'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Software Engineer")
        self.assertContains(response, "Remote Developer")
        self.assertNotContains(response, "Marketing Specialist")

    def test_search_by_salary_max_only(self):
        url = reverse('search_jobs')
        response = self.client.get(url, {'salary_max': '65000'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Marketing Specialist")
        self.assertNotContains(response, "Software Engineer")
        self.assertNotContains(response, "Remote Developer")

    def test_search_no_filters(self):
        url = reverse('search_jobs')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Software Engineer")
        self.assertContains(response, "Marketing Specialist")
        self.assertContains(response, "Remote Developer")

    def test_search_with_non_numeric_salary(self):
        url = reverse('search_jobs')
        response = self.client.get(url, {'salary_min': 'abc', 'salary_max': 'xyz'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Software Engineer")
        self.assertContains(response, "Marketing Specialist")
        self.assertContains(response, "Remote Developer")

    def test_search_with_empty_filters(self):
        url = reverse('search_jobs')
        response = self.client.get(url, {'industry': '', 'location': '', 'remote': ''})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Software Engineer")
        self.assertContains(response, "Marketing Specialist")
        self.assertContains(response, "Remote Developer")

    def test_search_with_invalid_remote_value(self):
        url = reverse('search_jobs')
        response = self.client.get(url, {'remote': 'invalid'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Software Engineer")
        self.assertContains(response, "Marketing Specialist")
        self.assertContains(response, "Remote Developer")

    def test_search_with_negative_salary(self):
        url = reverse('search_jobs')
        response = self.client.get(url, {'salary_min': '-5000', 'salary_max': '-1000'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Software Engineer")
        self.assertContains(response, "Marketing Specialist")
        self.assertContains(response, "Remote Developer")

    def test_search_with_inverted_salary_range(self):
        url = reverse('search_jobs')
        response = self.client.get(url, {'salary_min': '70000', 'salary_max': '50000'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Software Engineer")
        self.assertContains(response, "Marketing Specialist")
        self.assertContains(response, "Remote Developer")

    def test_search_combined_filters(self):
        url = reverse('search_jobs')
        response = self.client.get(url, {
            'industry': 'Technology',
            'location': 'Remote',
            'remote': 'yes',
            'salary_min': '65000'
        })
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "Software Engineer")
        self.assertNotContains(response, "Marketing Specialist")
        self.assertContains(response, "Remote Developer")

    def test_search_combined_filters_no_results(self):
        url = reverse('search_jobs')
        response = self.client.get(url, {
            'industry': 'Technology',
            'location': 'London',
            'remote': 'no',
            'salary_min': '100000'
        })
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "Software Engineer")
        self.assertNotContains(response, "Marketing Specialist")
        self.assertNotContains(response, "Remote Developer")

    def test_search_case_insensitive(self):
        url = reverse('search_jobs')
        response = self.client.get(url, {'industry': 'technology'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Software Engineer")
        self.assertContains(response, "Remote Developer")
        self.assertNotContains(response, "Marketing Specialist")

class JobModelTests(TestCase):
    def test_job_string_representation(self):
        job = Job.objects.create(
            title="Test Job",
            description="Description",
            industry="Test Industry",
            location="Test Location"
        )
        self.assertEqual(str(job), "Test Job")