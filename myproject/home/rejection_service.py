import os
import json
from typing import List, Dict, Any, Optional
import requests
from django.conf import settings

class RejectionService:
    """Service to generate potential rejection reasons for a job application using OpenAI"""

    # configuring API
    API_URL = "https://api.openai.com/v1/chat/completions"

    # Getting API key from environment or settings
    @staticmethod
    def get_api_key():
        api_key = os.environ.get('OPENAI_API_KEY')

        if not api_key and hasattr(settings, 'OPENAI_API_KEY'):
            api_key = settings.OPENAI_API_KEY

        return api_key

    @staticmethod
    def generate_rejection_reasons_resume(resume_text: str, job_description: Optional[str] = None) -> Dict[str, Any]:
        """Evaluate interview response using OpenAI API"""
        # hardcoded feedback as fallback
        generic_feedback = {
            "generic feedback fr"
        }

        try:
            api_key = RejectionService.get_api_key()

            if not api_key:
                print("OpenAI API key not found. Using generic feedback.")
                return generic_feedback

            # preparing the prompt
            prompt = ""
            if job_description:
                prompt += f"Job Description: {job_description}\n\n"
            resume_prompt = "User doesn't have a resume on their profile\n\n"
            if len(resume_text) > 0:
                resume_prompt = f"User's Resume: {resume_text}\n\n"
            prompt += resume_prompt

            # setting up the API request
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}"
            }

            data = {
                "model": "gpt-4o",
                "messages": [
                    {"role": "system", "content": "You are a helpful assistant that evaluates job applications. When provided with a job description and a resume, analyze the two and generate potential rejection reasons based on mismatches between the job requirements and the applicant's qualifications. Consider missing qualifications, lack of relevant experience, skills mismatch, and any other relevant factors that could affect the applicant's fit for the job."},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.7,
                "max_tokens": 1000
            }

            # making the API call
            response = requests.post(
                RejectionService.API_URL,
                headers=headers,
                json=data
            )

            # checking for successful response
            if response.status_code == 200:
                result = response.json()
                content = result["choices"][0]["message"]["content"]
                return content

            # logging API error and return generic feedback
            print(f"OpenAI API error: {response.status_code}, {response.text}")
            return generic_feedback

        except Exception as e:
            print(f"Error evaluating response: {str(e)}")
            return generic_feedback