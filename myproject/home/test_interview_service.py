import os
from django.test import TestCase, override_settings
from unittest.mock import patch, MagicMock
import requests
import json

from home.interview_service import InterviewService

MOCK_QUESTIONS_RESPONSE_JSON = {
    "id": "chatcmpl-123",
    "object": "chat.completion",
    "created": 1677652288,
    "model": "gpt-4o-xxx",
    "choices": [
        {
            "index": 0,
            "message": {
                "role": "assistant",
                "content": json.dumps([
                    "Mock Question 1?",
                    "Mock Question 2!",
                    "Tell me about Mock 3."
                ])
            },
            "finish_reason": "stop"
        }
    ],
    "usage": {"prompt_tokens": 9, "completion_tokens": 12, "total_tokens": 21}
}

MOCK_QUESTIONS_RESPONSE_TEXT = {
     "id": "chatcmpl-124",
     "object": "chat.completion",
     "created": 1677652289,
     "model": "gpt-4o-xxx",
     "choices": [
         {
             "index": 0,
             "message": {
                 "role": "assistant",
                 "content": "1. Mock Text Q1?\n2. Mock Text Q2!\n- Mock Text Q3."
             },
             "finish_reason": "stop"
         }
     ],
     "usage": {"prompt_tokens": 10, "completion_tokens": 15, "total_tokens": 25}
 }

MOCK_EVAL_RESPONSE_JSON = {
    "id": "chatcmpl-125",
    "object": "chat.completion",
    "created": 1677652290,
    "model": "gpt-4o-xxx",
    "choices": [
        {
            "index": 0,
            "message": {
                "role": "assistant",
                "content": json.dumps({
                    "score": 8,
                    "strengths": ["Clear communication", "Good examples"],
                    "areas_to_improve": ["More detail needed"],
                    "suggestions": "Expand on project X."
                })
            },
            "finish_reason": "stop"
        }
    ],
    "usage": {"prompt_tokens": 50, "completion_tokens": 60, "total_tokens": 110}
}

MOCK_EVAL_MALFORMED_JSON = {
    "id": "chatcmpl-126",
    "object": "chat.completion",
    "created": 1677652291,
    "model": "gpt-4o-xxx",
    "choices": [
        {
            "index": 0,
            "message": {
                "role": "assistant",
                "content": "{'score': 7, 'strengths': ['Okay']"
            },
            "finish_reason": "stop"
        }
    ],
    "usage": {"prompt_tokens": 50, "completion_tokens": 30, "total_tokens": 80}
}

MOCK_EVAL_MISSING_KEYS = {
     "id": "chatcmpl-127",
     "object": "chat.completion",
     "created": 1677652292,
     "model": "gpt-4o-xxx",
     "choices": [
         {
             "index": 0,
             "message": {
                 "role": "assistant",
                 "content": json.dumps({
                     "score": 9
                 })
             },
             "finish_reason": "stop"
         }
     ],
     "usage": {"prompt_tokens": 50, "completion_tokens": 10, "total_tokens": 60}
 }

GENERIC_QUESTIONS = [
    "Tell me about yourself and why you're interested in this position.",
    "What experience do you have that's relevant to this role?",
    "How would you handle a situation where you had conflicting priorities?",
    "What are your greatest strengths and how would they benefit this role?",
    "Do you have any questions about the company or position?"
]

GENERIC_FEEDBACK = {
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

class InterviewServiceTests(TestCase):

    @patch.dict(os.environ, {"OPENAI_API_KEY": "env_key_123"})
    @override_settings(OPENAI_API_KEY="settings_key_456")
    def test_get_api_key_from_env(self):
        self.assertEqual(InterviewService.get_api_key(), "env_key_123")

    @patch.dict(os.environ, {}, clear=True)
    @override_settings(OPENAI_API_KEY="settings_key_456")
    def test_get_api_key_from_settings(self):
        self.assertEqual(InterviewService.get_api_key(), "settings_key_456")

    @patch.dict(os.environ, {}, clear=True)
    @override_settings()
    def test_get_api_key_not_found(self):
        self.assertIsNone(InterviewService.get_api_key())

    @patch('home.interview_service.requests.post')
    @patch.dict(os.environ, {"OPENAI_API_KEY": "fake_key"})
    def test_generate_questions_success_json(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = MOCK_QUESTIONS_RESPONSE_JSON
        mock_post.return_value = mock_response

        questions = InterviewService.generate_interview_questions("Job desc", num_questions=3)

        mock_post.assert_called_once()
        self.assertEqual(len(questions), 3)
        self.assertEqual(questions, ["Mock Question 1?", "Mock Question 2!", "Tell me about Mock 3."])

    @patch('home.interview_service.requests.post')
    @patch.dict(os.environ, {"OPENAI_API_KEY": "fake_key"})
    def test_generate_questions_success_text(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = MOCK_QUESTIONS_RESPONSE_TEXT
        mock_post.return_value = mock_response

        questions = InterviewService.generate_interview_questions("Job desc", num_questions=3)

        mock_post.assert_called_once()
        self.assertEqual(len(questions), 3)
        self.assertEqual(questions, ["Mock Text Q1?", "Mock Text Q2!", "Mock Text Q3."])

    @patch('home.interview_service.requests.post')
    @patch.dict(os.environ, {}, clear=True)
    def test_generate_questions_no_api_key(self, mock_post):
        questions = InterviewService.generate_interview_questions("Job desc")
        mock_post.assert_not_called()
        self.assertEqual(questions, GENERIC_QUESTIONS)

    @patch('home.interview_service.requests.post')
    @patch.dict(os.environ, {"OPENAI_API_KEY": "fake_key"})
    def test_generate_questions_api_http_error(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError("Server Error")
        mock_response.text = "Internal Server Error"
        mock_post.return_value = mock_response

        questions = InterviewService.generate_interview_questions("Job desc")
        mock_post.assert_called_once()
        self.assertEqual(questions, GENERIC_QUESTIONS)

    @patch('home.interview_service.requests.post')
    @patch.dict(os.environ, {"OPENAI_API_KEY": "fake_key"})
    def test_generate_questions_api_request_exception(self, mock_post):
        mock_post.side_effect = requests.exceptions.RequestException("Network Error")

        questions = InterviewService.generate_interview_questions("Job desc")
        mock_post.assert_called_once()
        self.assertEqual(questions, GENERIC_QUESTIONS)

    @patch('home.interview_service.requests.post')
    @patch.dict(os.environ, {"OPENAI_API_KEY": "fake_key"})
    def test_generate_questions_json_decode_error(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'choices': [{'message': {'content': '[Invalid JSON:'}}]}
        mock_post.return_value = mock_response

        with patch('json.loads', side_effect=json.JSONDecodeError("Mock error", "doc", 0)):
            questions = InterviewService.generate_interview_questions("Job desc")

        mock_post.assert_called_once()
        self.assertEqual(questions, GENERIC_QUESTIONS)

    @patch('home.interview_service.requests.post')
    @patch.dict(os.environ, {"OPENAI_API_KEY": "fake_key"})
    def test_evaluate_response_success(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = MOCK_EVAL_RESPONSE_JSON
        mock_post.return_value = mock_response

        feedback = InterviewService.evaluate_response("Q?", "My Answer", "Job Desc")
        mock_post.assert_called_once()
        expected_feedback = json.loads(MOCK_EVAL_RESPONSE_JSON['choices'][0]['message']['content'])
        self.assertEqual(feedback, expected_feedback)

    @patch('home.interview_service.requests.post')
    @patch.dict(os.environ, {}, clear=True) # No API key
    def test_evaluate_response_no_api_key(self, mock_post):
        """Test fallback to generic feedback when no API key is found."""
        feedback = InterviewService.evaluate_response("Q?", "My Answer")
        mock_post.assert_not_called()
        self.assertEqual(feedback, GENERIC_FEEDBACK)

    @patch('home.interview_service.requests.post')
    @patch.dict(os.environ, {"OPENAI_API_KEY": "fake_key"})
    def test_evaluate_response_api_http_error(self, mock_post):
        """Test fallback to generic feedback on API HTTP error."""
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError("Server Error")
        mock_response.text = "Internal Server Error"
        mock_post.return_value = mock_response

        feedback = InterviewService.evaluate_response("Q?", "My Answer")
        mock_post.assert_called_once()
        self.assertEqual(feedback, GENERIC_FEEDBACK)

    @patch('home.interview_service.requests.post')
    @patch.dict(os.environ, {"OPENAI_API_KEY": "fake_key"})
    def test_evaluate_response_api_request_exception(self, mock_post):
        """Test fallback to generic feedback on requests exception."""
        mock_post.side_effect = requests.exceptions.RequestException("Network Error")

        feedback = InterviewService.evaluate_response("Q?", "My Answer")
        mock_post.assert_called_once()
        self.assertEqual(feedback, GENERIC_FEEDBACK)

    @patch('home.interview_service.requests.post')
    @patch.dict(os.environ, {"OPENAI_API_KEY": "fake_key"})
    def test_evaluate_response_malformed_json(self, mock_post):
        """Test fallback to generic feedback on malformed JSON response."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = MOCK_EVAL_MALFORMED_JSON
        mock_post.return_value = mock_response

        feedback = InterviewService.evaluate_response("Q?", "My Answer")
        mock_post.assert_called_once()
        self.assertEqual(feedback, GENERIC_FEEDBACK)

    @patch('home.interview_service.requests.post')
    @patch.dict(os.environ, {"OPENAI_API_KEY": "fake_key"})
    def test_evaluate_response_missing_keys(self, mock_post):
        """Test fallback to generic feedback when response JSON misses required keys."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = MOCK_EVAL_MISSING_KEYS
        mock_post.return_value = mock_response

        feedback = InterviewService.evaluate_response("Q?", "My Answer")
        mock_post.assert_called_once()
        self.assertEqual(feedback, GENERIC_FEEDBACK)

    @patch('home.interview_service.requests.post')
    @patch.dict(os.environ, {"OPENAI_API_KEY": "fake_key"})
    def test_evaluate_response_non_numeric_score(self, mock_post):
        """Test handling of non-numeric score, defaulting to 7."""
        response_content = {
            "score": "Not A Number",
            "strengths": [],
            "areas_to_improve": [],
            "suggestions": "Test"
        }
        mock_response_data = {
             "choices": [{"message": {"content": json.dumps(response_content)}}]
         }
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_response_data
        mock_post.return_value = mock_response

        feedback = InterviewService.evaluate_response("Q?", "My Answer")
        mock_post.assert_called_once()
        self.assertEqual(feedback['score'], 7) # Should default to 7
        self.assertEqual(feedback['suggestions'], "Test")

    @patch('home.interview_service.requests.post')
    @patch.dict(os.environ, {"OPENAI_API_KEY": "fake_key"})
    def test_evaluate_response_json_decode_error(self, mock_post):
        """Test fallback to generic feedback on JSONDecodeError."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = MOCK_EVAL_MALFORMED_JSON # Use the malformed mock
        mock_post.return_value = mock_response

        # Patch json.loads specific to the call inside evaluate_response
        with patch('json.loads', side_effect=json.JSONDecodeError("Mock error", "doc", 0)):
            feedback = InterviewService.evaluate_response("Q?", "My Answer")

        mock_post.assert_called_once()
        self.assertEqual(feedback, GENERIC_FEEDBACK)

    @patch('home.interview_service.requests.post')
    @patch.dict(os.environ, {"OPENAI_API_KEY": "fake_key"})
    def test_evaluate_response_no_json_object_found(self, mock_post):
        """Test fallback when API response content has no JSON object markers ({ })."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'choices': [{'message': {'content': 'Just plain text feedback.'}}]}
        mock_post.return_value = mock_response

        feedback = InterviewService.evaluate_response("Q?", "My Answer")
        mock_post.assert_called_once()
        self.assertEqual(feedback, GENERIC_FEEDBACK)

    @patch('home.interview_service.requests.post')
    @patch.dict(os.environ, {"OPENAI_API_KEY": "fake_key"})
    def test_evaluate_response_score_clamping(self, mock_post):
        """Test score clamping between 1 and 10."""
        # Score too low
        content_low = json.dumps({"score": 0, "strengths": [], "areas_to_improve": [], "suggestions": ""})
        mock_response_low = MagicMock(status_code=200, json=lambda: {'choices': [{'message': {'content': content_low}}]})
        mock_post.return_value = mock_response_low
        feedback_low = InterviewService.evaluate_response("Q?", "Low Score Answer")
        self.assertEqual(feedback_low['score'], 1)

        # Score too high
        content_high = json.dumps({"score": 15, "strengths": [], "areas_to_improve": [], "suggestions": ""})
        mock_response_high = MagicMock(status_code=200, json=lambda: {'choices': [{'message': {'content': content_high}}]})
        mock_post.return_value = mock_response_high
        feedback_high = InterviewService.evaluate_response("Q?", "High Score Answer")
        self.assertEqual(feedback_high['score'], 10)

        # Score is valid integer
        content_valid = json.dumps({"score": 5, "strengths": [], "areas_to_improve": [], "suggestions": ""})
        mock_response_valid = MagicMock(status_code=200, json=lambda: {'choices': [{'message': {'content': content_valid}}]})
        mock_post.return_value = mock_response_valid
        feedback_valid = InterviewService.evaluate_response("Q?", "Valid Score Answer")
        self.assertEqual(feedback_valid['score'], 5)