"""
This file contains the tests for the home app.
"""

from unittest.mock import patch, MagicMock
from datetime import datetime

from django.test import TestCase
from django.utils import timezone

import requests

from home.services import JobicyService # pylint: disable=import-error,no-name-in-module
from home.models import JobListing # pylint: disable=import-error,no-name-in-module

MOCK_API_RESPONSE = {
    "jobs": [
        {
            "id": "job1",
            "jobTitle": "Test Job 1",
            "companyName": "TestCo",
            "companyLogo": "logo.png",
            "jobType": "full_time",
            "jobGeo": "Remote",
            "jobDescription": "Desc 1",
            "url": "test.com/job1",
            "jobIndustry": "Tech",
            "jobLevel": "Mid",
            "annualSalaryMin": 50000,
            "annualSalaryMax": 70000,
            "salaryCurrency": "USD",
            "pubDate": "2024-01-01 10:00:00"
        },
        {
            "id": "job2",
            "jobTitle": "Test Job 2",
            "companyName": "TestCorp",
            "jobType": "part_time",
            "jobGeo": "USA",
            "jobDescription": "Desc 2",
            "url": "test.com/job2",
            "pubDate": "2024-01-02 12:00:00"
        }
    ]
}

class JobicyServiceTests(TestCase):
    """
    This class contains the tests for the JobicyService class.
    """
    @patch('home.services.requests.get')
    def test_search_jobs_api_success(self, mock_get):
        """
        This test searches for jobs from the Jobicy API.
        """
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = MOCK_API_RESPONSE
        mock_get.return_value = mock_response

        search_term = "python"
        params = {'geo': 'usa', 'industry': 'tech'}
        cache_key = JobicyService._build_cache_key(search_term, params) # pylint: disable=protected-access

        self.assertEqual(JobListing.objects.count(), 0)

        jobs = JobicyService.search_jobs(search_term, params)

        mock_get.assert_called_once()
        self.assertEqual(len(jobs), 2)
        self.assertEqual(JobListing.objects.count(), 2)

        job1 = JobListing.objects.get(job_id='job1')
        self.assertEqual(job1.title, "Test Job 1")
        self.assertEqual(job1.company, "TestCo")
        self.assertEqual(job1.search_key, cache_key)
        expected_datetime = datetime(2024, 1, 1, 10, 0, 0, tzinfo=timezone.utc)
        self.assertEqual(job1.published_at, expected_datetime)

        job2 = JobListing.objects.get(job_id='job2')
        self.assertEqual(job2.title, "Test Job 2")
        self.assertEqual(job2.search_key, cache_key)
        self.assertIsNone(job2.company_logo)

    @patch('home.services.requests.get')
    def test_search_jobs_api_no_jobs_field(self, mock_get):
        """
        This test searches for jobs from the Jobicy API when the 'jobs' field is not present.
        """
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {"some_other_field": []}
        mock_get.return_value = mock_response

        jobs = JobicyService.search_jobs("java", None)

        mock_get.assert_called_once()
        self.assertEqual(len(jobs), 0)
        self.assertEqual(JobListing.objects.count(), 0)

    @patch('home.services.requests.get')
    def test_search_jobs_api_http_error(self, mock_get):
        """
        This test searches for jobs from the Jobicy API when the API returns an HTTP error.
        """
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError("API Down")
        mock_get.return_value = mock_response

        jobs = JobicyService.search_jobs("ruby", None)

        mock_get.assert_called_once()
        self.assertEqual(len(jobs), 0)
        self.assertEqual(JobListing.objects.count(), 0)

    @patch('home.services.requests.get')
    def test_search_jobs_api_request_exception(self, mock_get):
        """
        This test searches for jobs from the Jobicy API when the API returns a request exception.
        """
        mock_get.side_effect = requests.exceptions.RequestException("Network Error")

        jobs = JobicyService.search_jobs("go", None)

        mock_get.assert_called_once()
        self.assertEqual(len(jobs), 0)
        self.assertEqual(JobListing.objects.count(), 0)

    @patch('home.services.requests.get')
    def test_search_jobs_cache_hit(self, mock_get):
        """
        This test searches for jobs from the Jobicy API when the cache hits.
        """
        search_term = "cached"
        params = {'geo': 'usa', 'industry': 'tech'}

        cache_key = JobicyService._build_cache_key(search_term, params) # pylint: disable=protected-access

        cached_job = JobListing.objects.create(
            job_id='cached-job-1',
            title='Cached Job',
            company='Cache Inc.',
            search_key=cache_key,
            published_at=timezone.now()
        )
        jobs = JobicyService.search_jobs(search_term, params)

        mock_get.assert_not_called()

        self.assertEqual(len(jobs), 1)
        self.assertEqual(jobs[0], cached_job)
        self.assertEqual(JobListing.objects.count(), 1)

    def test_get_job_details_found(self):
        """
        This test gets job details from the Jobicy API when the job exists.
        """
        job = JobListing.objects.create(job_id='detail-job', title='Detail Job',
                                        company='Detail Co.')
        retrieved_job = JobicyService.get_job_details(job.job_id)
        self.assertEqual(retrieved_job, job)

    def test_get_job_details_not_found(self):
        """
        This test gets job details from the Jobicy API when the job does not exist.
        """
        retrieved_job = JobicyService.get_job_details('non-existent-id')
        self.assertIsNone(retrieved_job)

    def test_build_cache_key(self):
        """
        This test builds the cache key for the Jobicy API.
        """
        key1 = JobicyService._build_cache_key("Python", {"geo": "usa", "industry": "tech"}) # pylint: disable=protected-access
        key2 = JobicyService._build_cache_key("python", {"industry": "tech", "geo": "usa"}) # pylint: disable=protected-access
        key3 = JobicyService._build_cache_key("Python", {"geo": "remote"}) # pylint: disable=protected-access
        key4 = JobicyService._build_cache_key("Java", {"geo": "usa", "industry": "tech"}) # pylint: disable=protected-access
        key5 = JobicyService._build_cache_key("python", None) # pylint: disable=protected-access

        self.assertEqual(key1, "python:geo=usa&industry=tech")
        self.assertEqual(key1, key2)
        self.assertNotEqual(key1, key3)
        self.assertNotEqual(key1, key4)
        self.assertEqual(key5, "python:")
