import os
import json
from typing import List, Dict, Any, Optional
import requests
from django.conf import settings


class InterviewService:
    """Service to handle interview simulation using OpenAI"""

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
    def generate_interview_questions(job_description: str, num_questions: int = 5) -> List[str]:
        """Generate interview questions based on job description using OpenAI API"""
        # hardcoded questions as fallback
        generic_questions = [
            "Tell me about yourself and why you're interested in this position.",
            "What experience do you have that's relevant to this role?",
            "How would you handle a situation where you had conflicting priorities?",
            "What are your greatest strengths and how would they benefit this role?",
            "Do you have any questions about the company or position?"
        ]

        # trying to use OpenAI to generate job-specific questions
        try:
            api_key = InterviewService.get_api_key()

            if not api_key:
                print("OpenAI API key not found. Using generic questions.")
                return generic_questions

            # Preparing the prompt based on job description
            if job_description:
                prompt = f"Generate {num_questions} specific interview questions for a candidate applying to the following job:\n\n{job_description}\n\nOnly include the questions, with no numbering or additional text. Format as a JSON array."
            else:
                prompt = f"Generate {num_questions} general job interview questions. Only include the questions, with no numbering or additional text. Format as a JSON array."

            # Setting up the API request
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}"
            }

            data = {
                "model": "gpt-4o",
                "messages": [
                    {"role": "system",
                     "content": "You are an expert interviewer helping to generate relevant job interview questions based on a job description."},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.7,
                "max_tokens": 1000
            }

            # Making the API call
            response = requests.post(
                InterviewService.API_URL,
                headers=headers,
                json=data
            )

            # Checking for successful response
            if response.status_code == 200:
                result = response.json()
                content = result["choices"][0]["message"]["content"]

                # Trying to parse as JSON
                try:
                    # Extracting the JSON array if it's embedded in text
                    if '[' in content and ']' in content:
                        start = content.find('[')
                        end = content.rfind(']') + 1
                        json_content = content[start:end]
                        questions = json.loads(json_content)
                    else:
                        # If not in JSON format, splitting by newlines and cleaning up
                        questions = [q.strip() for q in content.split('\n') if q.strip()]

                    return questions[:num_questions]

                except json.JSONDecodeError:
                    # If JSON parsing fails, splitting by newlines and removing numbers
                    questions = []
                    for line in content.split('\n'):
                        line = line.strip()
                        if line and (line.startswith("- ") or (line[0].isdigit() and line[1:3] in ['. ', ') '])):
                            # Removing leading number
                            clean_line = line[line.find(' ') + 1:].strip()
                            questions.append(clean_line)
                        elif line and not line.startswith(('Here', 'These', 'The following')):
                            questions.append(line)

                    return questions[:num_questions] if questions else generic_questions

            # Log API error and return generic questions
            print(f"OpenAI API error: {response.status_code}, {response.text}")
            return generic_questions

        except Exception as e:
            print(f"Error generating questions: {str(e)}")
            return generic_questions

    @staticmethod
    def evaluate_response(question: str, response: str, job_description: Optional[str] = None) -> Dict[str, Any]:
        """Evaluate interview response using OpenAI API"""
        # hardcoded feedback as fallback
        generic_feedback = {
            "score": 7,
            "strengths": [
                "Good articulation of ideas",
                "Showed enthusiasm for the role"
            ],
            "areas_to_improve": [
                "Could provide more specific examples",
                "Consider addressing how your skills match the job requirements"
            ],
            "suggestions": "Try to be more specific about your experiences and how they relate to the job requirements. Quantify your achievements when possible."
        }

        try:
            api_key = InterviewService.get_api_key()

            if not api_key:
                print("OpenAI API key not found. Using generic feedback.")
                return generic_feedback

            # preparing the prompt
            context = f"Question: {question}\n\n"
            if job_description:
                context += f"Job Description: {job_description}\n\n"
            context += f"Candidate Response: {response}\n\n"

            prompt = context + "Evaluate this interview response. Provide: 1) a score from 1-10, 2) a list of strengths, 3) a list of areas to improve, and 4) concrete suggestions for improvement. Format your response as a JSON object with keys: 'score', 'strengths' (array), 'areas_to_improve' (array), and 'suggestions' (string)."

            # setting up the API request
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}"
            }

            data = {
                "model": "gpt-4o",
                "messages": [
                    {"role": "system", "content": "You are an expert interview coach evaluating candidate responses."},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.7,
                "max_tokens": 1000
            }

            # making the API call
            response = requests.post(
                InterviewService.API_URL,
                headers=headers,
                json=data
            )

            # checking for successful response
            if response.status_code == 200:
                result = response.json()
                content = result["choices"][0]["message"]["content"]

                # trying to parse as JSON
                try:
                    # extracting the JSON object
                    if '{' in content and '}' in content:
                        start = content.find('{')
                        end = content.rfind('}') + 1
                        json_content = content[start:end]
                        feedback = json.loads(json_content)

                        # validating the required keys
                        required_keys = ['score', 'strengths', 'areas_to_improve', 'suggestions']
                        for key in required_keys:
                            if key not in feedback:
                                print(f"Missing key in response: {key}")
                                return generic_feedback

                        # ensuring score is a number between 1-10
                        try:
                            feedback['score'] = int(feedback['score'])
                            feedback['score'] = max(1, min(10, feedback['score']))
                        except (ValueError, TypeError):
                            feedback['score'] = 7

                        return feedback
                    else:
                        print("No JSON object found in response")
                        return generic_feedback

                except json.JSONDecodeError as e:
                    print(f"Error parsing JSON: {str(e)}")
                    return generic_feedback

            # logging API error and return generic feedback
            print(f"OpenAI API error: {response.status_code}, {response.text}")
            return generic_feedback

        except Exception as e:
            print(f"Error evaluating response: {str(e)}")
            return generic_feedback