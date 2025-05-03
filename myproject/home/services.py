"""
This file contains the services for the home app.
"""
import requests
from datetime import datetime
from typing import List, Optional, Dict, Any
from .models import JobListing
from django.utils import timezone
import urllib.parse

class JobicyService:
    """
    This class contains the services for the Jobicy API.
    """
    BASE_URL = "https://jobicy.com/api/v2/remote-jobs"

    @staticmethod
    def _build_cache_key(search_term: str, params: Optional[Dict[str, Any]] = None) -> str:
        """
        This function builds the cache key for the Jobicy API.
        """
        if params is None:
            params = {}

        param_str = "&".join(f"{k}={v}" for k, v in sorted(params.items()))
        return f"{search_term.lower()}:{param_str}"

    @staticmethod
    def fetch_and_cache_jobs(search_term: str,
                             params: Optional[Dict[str, Any]] = None) -> List[JobListing]:
        """
        This function fetches and caches the jobs from the Jobicy API.
        """
        url = f"{JobicyService.BASE_URL}?count=50"
        api_params = {}

        if search_term:
            api_params['tag'] = search_term

        if params:
            if params.get('jobType'):
                if search_term:
                    api_params['tag'] = f"{search_term} {params['jobType']}"
                else:
                    api_params['tag'] = params['jobType']

            if params.get('geo'):
                api_params['geo'] = params['geo'].lower()

            if params.get('jobIndustry'):
                api_params['industry'] = params['jobIndustry'].lower()

        for key, value in api_params.items():
            url = f"{url}&{key}={urllib.parse.quote(str(value))}"

        try:
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()

            if not data.get('jobs'):
                return []

            cached_jobs = []
            cache_key = JobicyService._build_cache_key(search_term, params)

            for job in data['jobs']:
                pub_date_str = job.get('pubDate')
                published_at_aware = None
                if pub_date_str:
                    try:
                        naive_dt = datetime.strptime(pub_date_str, "%Y-%m-%d %H:%M:%S")
                        published_at_aware = timezone.make_aware(naive_dt, timezone.utc)
                    except ValueError:
                        pass

                job_listing, created = JobListing.objects.get_or_create(
                    job_id=job['id'],
                    defaults={
                        'title': job.get('jobTitle'),
                        'company': job.get('companyName'),
                        'company_logo': job.get('companyLogo'),
                        'job_type': job.get('jobType'),
                        'location': job.get('jobGeo'),
                        'description': job.get('jobDescription'),
                        'url': job.get('url'),
                        'industry': job.get('jobIndustry'),
                        'job_level': job.get('jobLevel'),
                        'salary_min': job.get('annualSalaryMin'),
                        'salary_max': job.get('annualSalaryMax'),
                        'salary_currency': job.get('salaryCurrency'),
                        'search_key': cache_key,
                        'published_at': published_at_aware,
                    }
                )

                if not created:
                    job_listing.search_key = cache_key
                    if published_at_aware:
                        job_listing.published_at = published_at_aware
                    job_listing.save(update_fields=['search_key', 'published_at'])

                cached_jobs.append(job_listing)

            return cached_jobs

        except requests.exceptions.RequestException:
            return []

    @staticmethod
    def search_jobs(search_term: str, params: Optional[Dict[str, Any]] = None) -> List[JobListing]:
        cache_key = JobicyService._build_cache_key(search_term, params)
        cached_jobs = JobListing.objects.filter(search_key=cache_key)

        if cached_jobs.exists():
            return list(cached_jobs)

        return JobicyService.fetch_and_cache_jobs(search_term, params)

    @staticmethod
    def get_job_details(job_id: int) -> Optional[JobListing]:
        try:
            return JobListing.objects.get(job_id=job_id)
        except JobListing.DoesNotExist:
            return None
        except Exception:
            return None
