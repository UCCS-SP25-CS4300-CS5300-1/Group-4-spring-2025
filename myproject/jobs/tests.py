from django.test import TestCase, Client
from django.urls import reverse
from .models import Job

# Create your tests here.

class JobSearchTests(TestCase):
    def setUp(self):
        # initializing the test client
        self.client = Client()
        # creating some sample Job instances
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
        # expecting job1 and job3 (technology) to appear
        self.assertContains(response, "Software Engineer")
        self.assertContains(response, "Remote Developer")
        # ensuring job2 (marketing) is not included
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
        # only jobs with is_remote=True should be present
        self.assertContains(response, "Software Engineer")
        self.assertContains(response, "Remote Developer")
        self.assertNotContains(response, "Marketing Specialist")

    def test_search_by_salary_range(self):
        url = reverse('search_jobs')
        # looking for jobs with a minimum salary of 60000 and maximum salary of 90000
        response = self.client.get(url, {'salary_min': '60000', 'salary_max': '90000'})
        self.assertEqual(response.status_code, 200)
        
        ## Only "Remote Developer" should be returned because:
        ## - It has salary_min=70000 which is in the range 60000-90000
        ## - It has salary_max=100000 which overlaps with the range 60000-90000
        
        ## Software Engineer (50000-80000) should NOT be in the results because
        ## the test is specifically filtering for jobs with their salary_min at least 60000
        self.assertNotContains(response, "Software Engineer")
        
        ## Marketing Specialist (40000-60000) should NOT be in the results because
        ## its salary_max is below the requested minimum
        self.assertNotContains(response, "Marketing Specialist")
        
        ## Remote Developer (70000-100000) should be in the results because
        ## its salary falls within the requested range
        self.assertContains(response, "Remote Developer")

    def test_search_by_salary_min_only(self):
        url = reverse('search_jobs')
        response = self.client.get(url, {'salary_min': '45000'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Software Engineer")  ## 50000
        self.assertContains(response, "Remote Developer")   ## 70000
        ## Jobs with min salary < 45000 should not be in results
        self.assertNotContains(response, "Marketing Specialist")  ## 40000

    def test_search_by_salary_max_only(self):
        url = reverse('search_jobs')
        response = self.client.get(url, {'salary_max': '65000'})
        self.assertEqual(response.status_code, 200)
        ## Jobs with max salary <= 65000 should be in results
        self.assertContains(response, "Marketing Specialist")  ## 60000
        ## Jobs with max salary > 65000 should not be in results
        self.assertNotContains(response, "Software Engineer")  ## 80000
        self.assertNotContains(response, "Remote Developer")   ## 100000

    def test_search_no_filters(self):
        url = reverse('search_jobs')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        ## All jobs should be present when no filters are applied
        self.assertContains(response, "Software Engineer")
        self.assertContains(response, "Marketing Specialist")
        self.assertContains(response, "Remote Developer")

    def test_search_with_non_numeric_salary(self):
        """Test search with non-numeric salary values"""
        url = reverse('search_jobs')
        response = self.client.get(url, {'salary_min': 'abc', 'salary_max': 'xyz'})
        self.assertEqual(response.status_code, 200)
        ## All jobs should be present since invalid filters are ignored
        self.assertContains(response, "Software Engineer")
        self.assertContains(response, "Marketing Specialist")
        self.assertContains(response, "Remote Developer")
    
    def test_search_with_empty_filters(self):
        """Test search with empty but provided filter parameters"""
        url = reverse('search_jobs')
        response = self.client.get(url, {'industry': '', 'location': '', 'remote': ''})
        self.assertEqual(response.status_code, 200)
        ##   All jobs should be present when empty filters are applied
        self.assertContains(response, "Software Engineer")
        self.assertContains(response, "Marketing Specialist")
        self.assertContains(response, "Remote Developer")

class JobModelTests(TestCase):
    def test_job_string_representation(self):
        job = Job.objects.create(
            title="Test Job",
            description="Description",
            industry="Test Industry",
            location="Test Location"
        )
        self.assertEqual(str(job), "Test Job")