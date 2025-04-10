import requests
from datetime import datetime
from typing import List, Optional, Dict, Any
from .models import JobListing

class JobicyService:
    BASE_URL = "https://jobicy.com/api/v2/remote-jobs"

    @staticmethod
    def _build_cache_key(search_term: str, params: Optional[Dict[str, Any]] = None) -> str:
        """Build a unique cache key based on search parameters"""
        if params is None:
            params = {}
        
        # Sort params to ensure consistent cache keys
        param_str = "&".join(f"{k}={v}" for k, v in sorted(params.items()))
        return f"{search_term.lower()}:{param_str}"

    @staticmethod
    def fetch_and_cache_jobs(search_term: str, params: Optional[Dict[str, Any]] = None) -> List[JobListing]:
        """
        Fetch jobs from Jobicy API and cache them in the database
        Example URL: https://jobicy.com/api/v2/remote-jobs?count=50&tag=python
        """
        url = f"{JobicyService.BASE_URL}?count=50"
        
        if search_term:
            url = f"{url}&tag={search_term}"
            
        if params:
            for key, value in params.items():
                url = f"{url}&{key}={value}"

        try:
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()
            
            if 'jobs' not in data:
                print("No jobs field in response")
                return []

            cached_jobs = []
            cache_key = JobicyService._build_cache_key(search_term, params)

            for job in data['jobs']:
                job_listing, created = JobListing.objects.get_or_create(
                    job_id=job['id'],
                    defaults={
                        'title': job['jobTitle'],
                        'company': job['companyName'],
                        'company_logo': job.get('companyLogo', ''),
                        'job_type': job['jobType'],
                        'location': job['jobGeo'],
                        'description': job['jobDescription'],
                        'url': job['url'],
                        'salary_min': job.get('annualSalaryMin'),
                        'salary_max': job.get('annualSalaryMax'),
                        'salary_currency': job.get('salaryCurrency'),
                        'published_at': datetime.strptime(job['pubDate'], "%Y-%m-%d %H:%M:%S"),
                        'search_key': cache_key,
                    }
                )
                
                # Update search key for existing entries to mark them as part of this search
                if not created:
                    job_listing.search_key = cache_key
                    job_listing.save(update_fields=['search_key'])
                
                cached_jobs.append(job_listing)

            return cached_jobs

        except Exception as e:
            print(f"Error fetching jobs: {e}")
            return []

    @staticmethod
    def search_jobs(search_term: str, params: Optional[Dict[str, Any]] = None) -> List[JobListing]:
        """
        Search for jobs using the given search term and parameters
        Always check cache first, only fetch if no cached results exist
        """
        cache_key = JobicyService._build_cache_key(search_term, params)

        cached_results = JobListing.objects.filter(search_key=cache_key)

        if cached_results.exists():
            return list(cached_results)

        return JobicyService.fetch_and_cache_jobs(search_term, params) 