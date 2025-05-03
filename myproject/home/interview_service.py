import os
import json
import re
from typing import List, Dict, Any, Optional
import requests
from django.conf import settings

GENERIC_QUESTIONS = [
    "Tell me about yourself and why you're interested in this position.",
    "What experience do you have that's relevant to this role?",
    "How would you handle a situation where you had conflicting priorities?",
    "What are your greatest strengths and how would they benefit this role?",
    "Do you have any questions about the company or position?"
]

class InterviewService:
    API_URL = "https://api.openai.com/v1/chat/completions"

    @staticmethod
    def get_api_key():
        api_key = os.environ.get('OPENAI_API_KEY')


        if not api_key and hasattr(settings, 'OPENAI_API_KEY'):
            api_key = settings.OPENAI_API_KEY


        return api_key

    @staticmethod
    def _parse_questions_from_text(content: str, num_questions: int,
                                   generic_questions: list) -> List[str]:
        """
        This function parses the questions from the text.
        """
        questions = []
        marker_found = False
        list_marker_regex = re.compile(r"^\s*(?:\d+[\.\)]|[-*])\s*")

        lines = content.split('\n')
        for line in lines:
            line = line.strip()
            if line and not line.startswith(('Here', 'These', 'The following', '```', '[', '{')):
                clean_line = list_marker_regex.sub('', line).strip()
                if clean_line != line:
                    marker_found = True
                if clean_line:
                    questions.append(clean_line)

        if not questions or (questions and not marker_found):
             if len(questions) == 1 and not marker_found:
                 return questions[:num_questions]
             else:
                 return generic_questions
        else:
             return questions[:num_questions]

    @staticmethod
    def generate_interview_questions(job_description: str, num_questions: int = 5) -> List[str]:
        try:
            api_key = InterviewService.get_api_key()

            if not api_key:
                return GENERIC_QUESTIONS

            if job_description:
                prompt = (
                    f"Generate {num_questions} specific interview questions "
                    f"for a candidate applying to the following job:\n\n"
                    f"{job_description}\n\n"
                    "Only include the questions, with no numbering or additional text. "
                    "Format as a JSON array."
                )
            else:
                prompt = (
                    f"Generate {num_questions} general job interview questions. "
                    "Only include the questions, with no numbering or additional text. "
                    "Format as a JSON array."
                )

            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}"
            }

            data = {
                "model": "gpt-4o",
                "messages": [
                    {"role": "system",
                     "content": "You are an expert interviewer "
                               "helping to generate relevant "
                               "job interview questions "
                               "based on a job description."},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.7,
                "max_tokens": 1000
            }

            response = requests.post(
                InterviewService.API_URL,
                headers=headers,
                json=data
            )

            if response.status_code == 200:
                result = response.json()
                content = result["choices"][0]["message"]["content"]

                try:
                    if '[' in content and ']' in content:
                        start = content.find('[')
                        end = content.rfind(']') + 1
                        json_content = content[start:end]
                        questions = json.loads(json_content)
                        if isinstance(questions, list) \
                        and all(isinstance(q, str) for q in questions):
                            return questions[:num_questions]
                        else:
                            return InterviewService._parse_questions_from_text(content, 
                                                                               num_questions, 
                                                                               GENERIC_QUESTIONS)
                    else:
                        return InterviewService._parse_questions_from_text(content, 
                                                                           num_questions, 
                                                                           GENERIC_QUESTIONS)

                except json.JSONDecodeError:
                    return InterviewService._parse_questions_from_text(content, 
                                                                       num_questions, 
                                                                       GENERIC_QUESTIONS)

            return GENERIC_QUESTIONS

        except Exception as e:
            return GENERIC_QUESTIONS

    @staticmethod
    def evaluate_response(question: str, 
                          response: str, 
                          job_description: Optional[str] = None) -> Dict[str, Any]:
        """
        This function evaluates the response to the question.
        """
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
            "suggestions": "Try to be more specific about your experiences "
                           "and how they relate to the job requirements. "
                           "Quantify your achievements when possible."
        }

        try:
            api_key = InterviewService.get_api_key()

            if not api_key:
                return generic_feedback

            context = f"Question: {question}\n\n"
            if job_description:
                context += f"Job Description: {job_description}\n\n"
            context += f"Candidate Response: {response}\n\n"

            prompt = context + "Evaluate this interview response. Provide: 1) a score from 1-10, 2) a list of strengths, 3) a list of areas to improve, and 4) concrete suggestions for improvement. Format your response as a JSON object with keys: 'score', 'strengths' (array), 'areas_to_improve' (array), and 'suggestions' (string)."

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

            response = requests.post(
                InterviewService.API_URL,
                headers=headers,
                json=data
            )

            if response.status_code == 200:
                result = response.json()
                content = result["choices"][0]["message"]["content"]

                try:
                    if '{' in content and '}' in content:
                        start = content.find('{')
                        end = content.rfind('}') + 1
                        json_content = content[start:end]
                        feedback = json.loads(json_content)

                        required_keys = ['score', 'strengths', 'areas_to_improve', 'suggestions']
                        for key in required_keys:
                            if key not in feedback:
                                return generic_feedback

                        try:
                            feedback['score'] = int(feedback['score'])
                            feedback['score'] = max(1, min(10, feedback['score']))
                        except (ValueError, TypeError):
                            feedback['score'] = 7

                        return feedback
                    else:
                        return generic_feedback

                except json.JSONDecodeError as e:
                    return generic_feedback

            return generic_feedback

        except Exception as e:
            return generic_feedback