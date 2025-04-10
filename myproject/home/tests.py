from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from users.models import Profile
from home.models import Application, JobListing
from .forms import SearchJobForm, InterviewResponseForm
from django.utils import timezone
from unittest.mock import patch


class HomeViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.home_url = reverse('index')
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='StrongTestPass123'
        )

    def test_home_view_GET(self):
        response = self.client.get(self.home_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'home/index.html')

    def test_home_view_contains_expected_content(self):
        response = self.client.get(self.home_url)
        self.assertContains(response, '<title>ApplierPilotAI - Your AI Job Application Assistant</title>')
        self.assertContains(response, 'Supercharge Your Job Applications with AI')
        self.assertContains(response, 'AI-Powered Application Tools')
        self.assertContains(response, 'How Our AI Tools Help You')

        self.assertContains(response, '<a href="#features">Features</a>')
        self.assertContains(response, '<a href="#how-it-works">How It Works</a>')
        self.assertContains(response, '<a href="#contact">Contact</a>')
        self.assertNotContains(response, '<a href="#about">About</a>')

        self.assertContains(response, 'contact@ApplierPilot.com')
        self.assertNotContains(response, 'Pricing')

    def test_home_view_authenticated_user(self):
        self.client.login(username='testuser', password='StrongTestPass123')
        response = self.client.get(self.home_url)

        self.assertContains(response, 'Hello, testuser')
        self.assertContains(response, 'Logout')
        self.assertContains(response, 'Access AI Tools')
        self.assertContains(response, 'href="/dashboard/"')

        self.assertNotContains(response, 'class="login-btn"')
        self.assertNotContains(response, 'Start Using AI Tools')

    def test_home_view_unauthenticated_user(self):
        response = self.client.get(self.home_url)

        self.assertContains(response, 'Login')
        self.assertContains(response, 'Sign Up')
        self.assertContains(response, 'Start Using AI Tools')

        self.assertNotContains(response, 'Hello, testuser')
        self.assertNotContains(response, 'Access AI Tools')


class DashboardViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.dashboard_url = reverse('dashboard')

        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='StrongTestPass123'
        )

        self.profile = Profile.objects.get(user=self.user)
        self.profile.save()

        # Create some job listings for testing
        self.job1 = JobListing.objects.create(
            job_id='test-job-1',
            title='Senior Python Developer',
            company='Test Company',
            location='Remote',
            description='Test job description',
            url='https://example.com/job1',
            job_type='Full-time',
            published_at=timezone.now(),
            search_key='python'
        )

        self.job2 = JobListing.objects.create(
            job_id='test-job-2',
            title='Data Scientist',
            company='Another Company',
            location='New York',
            description='Another test job description',
            url='https://example.com/job2',
            job_type='Remote',
            published_at=timezone.now(),
            search_key='data-science'
        )

    def test_dashboard_login_required(self):
        """Test that unauthenticated users are redirected to login"""
        response = self.client.get(self.dashboard_url)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith('/users/login/'))
        self.assertTrue('next=/dashboard/' in response.url)

    def test_dashboard_authenticated_user(self):
        """Test that authenticated users can access the dashboard"""
        self.client.login(username='testuser', password='StrongTestPass123')
        response = self.client.get(self.dashboard_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'home/dashboard.html')

    def test_dashboard_context_data(self):
        """Test that the dashboard contains correct context data"""
        self.client.login(username='testuser', password='StrongTestPass123')
        response = self.client.get(self.dashboard_url)

        self.assertIsInstance(response.context['form'], SearchJobForm)
        self.assertIn('job_list', response.context)
        self.assertEqual(len(response.context['job_list']), 0)  # Empty by default

    def test_dashboard_search_results(self):
        """Test that the dashboard displays search results"""
        self.client.login(username='testuser', password='StrongTestPass123')

        # Mock the JobicyService.search_jobs method
        with patch('home.services.JobicyService.search_jobs') as mock_search:
            mock_search.return_value = [self.job1]

            response = self.client.post(self.dashboard_url, {'search_term': 'python'})

            self.assertEqual(response.status_code, 200)
            self.assertTemplateUsed(response, 'home/dashboard.html')
            self.assertIsInstance(response.context['form'], SearchJobForm)
            self.assertIn('job_list', response.context)
            self.assertEqual(len(response.context['job_list']), 1)

            # Verify the job details are displayed
            self.assertContains(response, 'Senior Python Developer')
            self.assertContains(response, 'Test Company')
            self.assertContains(response, 'Remote')

    def test_dashboard_form_validation_empty_search(self):
        """Test that empty search term is handled properly"""
        self.client.login(username='testuser', password='StrongTestPass123')
        response = self.client.post(self.dashboard_url, {'search_term': ''})
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'home/dashboard.html')
        self.assertTrue('form' in response.context)
        self.assertTrue(response.context['form'].errors)

    def test_dashboard_form_validation_missing_field(self):
        """Test that missing search term field is handled properly"""
        self.client.login(username='testuser', password='StrongTestPass123')
        response = self.client.post(self.dashboard_url, {})
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'home/dashboard.html')
        self.assertTrue('form' in response.context)
        self.assertTrue(response.context['form'].errors)

    def test_dashboard_displays_interview_coach_button(self):
        """Test that the dashboard shows Interview Coach button for job listings"""
        self.client.login(username='testuser', password='StrongTestPass123')

        # mocking the JobicyService.search_jobs method
        with patch('home.services.JobicyService.search_jobs') as mock_search:
            mock_search.return_value = [self.job1]

            response = self.client.post(self.dashboard_url, {'search_term': 'python'})
            self.assertContains(response, 'Interview Coach')
            self.assertContains(response, f'/interview-coach/{self.job1.job_id}/')

    def test_search_jobs_empty_function(self):
        """Test the empty search_jobs function"""
        self.client.login(username='testuser', password='StrongTestPass123')
        response = self.client.get(reverse('search_jobs'))
        self.assertEqual(response.status_code, 200)


class InterviewCoachViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.interview_coach_url = reverse('interview_coach')

        # creating a test user
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='StrongTestPass123'
        )

        self.profile = Profile.objects.get(user=self.user)
        self.profile.save()

        # creating a test job listing
        self.job = JobListing.objects.create(
            job_id='test-job-1',
            title='Senior Python Developer',
            company='Test Company',
            location='Remote',
            description='This job requires expertise in Python, Django, and API development.',
            url='https://example.com/job1',
            job_type='Full-time',
            published_at=timezone.now(),
            search_key='python'
        )

        # URL with job ID
        self.interview_coach_with_job_url = reverse('interview_coach_with_job', args=[self.job.job_id])

    def test_interview_coach_login_required(self):
        """Test that unauthenticated users are redirected to login"""
        response = self.client.get(self.interview_coach_url)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith('/users/login/'))

    def test_interview_coach_with_job_login_required(self):
        """Test that unauthenticated users are redirected when accessing interview with job"""
        response = self.client.get(self.interview_coach_with_job_url)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith('/users/login/'))

    def test_interview_coach_authenticated_user(self):
        """Test that authenticated users can access the interview coach"""
        # mocking the question generation
        with patch('home.interview_service.InterviewService.generate_interview_questions') as mock_generate_questions:
            mock_generate_questions.return_value = [
                "Tell me about yourself.",
                "What experience do you have with Python?"
            ]

            self.client.login(username='testuser', password='StrongTestPass123')
            response = self.client.get(self.interview_coach_url)

            self.assertEqual(response.status_code, 200)
            self.assertTemplateUsed(response, 'home/interview_coach.html')

            # checking that questions were generated
            self.assertIn('questions', response.context)
            self.assertEqual(len(response.context['questions']), 2)

            # verifying the mock was called correctly
            mock_generate_questions.assert_called_once_with("")

    def test_interview_coach_with_job_authenticated_user(self):
        """Test that authenticated users can access the interview coach with a job"""
        # mocking the question generation
        with patch('home.interview_service.InterviewService.generate_interview_questions') as mock_generate_questions:
            mock_generate_questions.return_value = [
                "Tell me about your experience with Python.",
                "How have you used Django in previous projects?"
            ]

            self.client.login(username='testuser', password='StrongTestPass123')
            response = self.client.get(self.interview_coach_with_job_url)

            self.assertEqual(response.status_code, 200)
            self.assertTemplateUsed(response, 'home/interview_coach.html')

            # checking that the job is in the context
            self.assertIn('job', response.context)
            self.assertEqual(response.context['job'], self.job)

            # checking that questions were generated
            self.assertIn('questions', response.context)
            self.assertEqual(len(response.context['questions']), 2)

            # verifying the mock was called with the job description
            mock_generate_questions.assert_called_once_with(self.job.description)

    def test_interview_coach_post_response(self):
        """testing submitting an interview response"""
        # mocking the evaluation response
        with patch('home.interview_service.InterviewService.evaluate_response') as mock_evaluate:
            mock_evaluate.return_value = {
                "score": 8,
                "strengths": ["Good communication", "Relevant experience"],
                "areas_to_improve": ["Be more specific"],
                "suggestions": "Provide concrete examples of your work."
            }

            self.client.login(username='testuser', password='StrongTestPass123')

            response = self.client.post(self.interview_coach_url, {
                'question': 'Tell me about yourself.',
                'response': 'I am a senior developer with 5 years of experience in Python.',
                'job_description': ''
            })

            self.assertEqual(response.status_code, 200)
            self.assertTemplateUsed(response, 'home/interview_coach.html')

            # checking that feedback is in the context
            self.assertIn('feedback', response.context)
            self.assertEqual(response.context['feedback']['score'], 8)

            # verifying the mock was called correctly
            mock_evaluate.assert_called_once_with(
                'Tell me about yourself.',
                'I am a senior developer with 5 years of experience in Python.',
                ''
            )

    def test_ajax_evaluate_response(self):
        """Test the AJAX endpoint for evaluating responses"""
        # mocking the evaluation response
        with patch('home.interview_service.InterviewService.evaluate_response') as mock_evaluate:
            mock_evaluate.return_value = {
                "score": 9,
                "strengths": ["Excellent communication", "Strong technical knowledge"],
                "areas_to_improve": ["Could provide more examples"],
                "suggestions": "Consider mentioning specific projects."
            }

            self.client.login(username='testuser', password='StrongTestPass123')

            response = self.client.post(
                reverse('evaluate_response'),
                {
                    'question': 'What experience do you have with Django?',
                    'response': 'I have built several web applications using Django over the past 3 years.',
                    'job_description': self.job.description
                },
                HTTP_X_REQUESTED_WITH='XMLHttpRequest'  # Simulates AJAX request
            )

            self.assertEqual(response.status_code, 200)
            self.assertEqual(response['Content-Type'], 'application/json')

            # parsing JSON response
            data = response.json()
            self.assertEqual(data['score'], 9)
            self.assertEqual(len(data['strengths']), 2)
            self.assertEqual(len(data['areas_to_improve']), 1)
            self.assertIn('suggestions', data)

            # verifying the mock was called correctly
            mock_evaluate.assert_called_once_with(
                'What experience do you have with Django?',
                'I have built several web applications using Django over the past 3 years.',
                self.job.description
            )

    def test_ajax_evaluate_response_validation(self):
        """testing validation in the AJAX endpoint"""
        self.client.login(username='testuser', password='StrongTestPass123')

        # testing with empty response
        response = self.client.post(
            reverse('evaluate_response'),
            {
                'question': 'What experience do you have with Django?',
                'response': '',  # Empty response
                'job_description': self.job.description
            },
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )

        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertIn('error', data)
        self.assertEqual(data['error'], 'Response is required')

        # testing without AJAX header
        response = self.client.post(
            reverse('evaluate_response'),
            {
                'question': 'What experience do you have with Django?',
                'response': 'Some response',
                'job_description': self.job.description
            }
        )

        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertIn('error', data)
        self.assertEqual(data['error'], 'Invalid request')


class InterviewServiceTest(TestCase):
    """tests for the InterviewService class"""

    def test_generate_interview_questions_fallback(self):
        """Test that generate_interview_questions returns fallback questions when API fails"""
        from home.interview_service import InterviewService
        
        # Force API failure by making openai.api_key None temporarily
        import openai
        original_key = openai.api_key
        openai.api_key = None
        
        try:
            # This should use fallback questions
            questions = InterviewService.generate_interview_questions("Test job description")
            
            # Verify we got some questions
            self.assertTrue(len(questions) > 0)
            self.assertTrue(isinstance(questions, list))
            self.assertTrue(all(isinstance(q, str) for q in questions))
            
            # Verify the first fallback question is present
            self.assertIn("Tell me about yourself", questions[0])
        finally:
            # Restore the API key
            openai.api_key = original_key

    def test_evaluate_response_fallback(self):
        """Test that evaluate_response returns fallback feedback when API fails"""
        from home.interview_service import InterviewService
        
        # Force API failure by making openai.api_key None temporarily
        import openai
        original_key = openai.api_key
        openai.api_key = None
        
        try:
            # This should use fallback feedback
            feedback = InterviewService.evaluate_response(
                "Tell me about yourself.",
                "I am a Python developer with 5 years of experience.",
                "Python Developer job description"
            )
            
            # Check structure of feedback
            self.assertIn('score', feedback)
            self.assertIn('strengths', feedback)
            self.assertIn('areas_to_improve', feedback)
            self.assertIn('suggestions', feedback)
            
            # Score should be between 1 and 10
            self.assertTrue(1 <= feedback['score'] <= 10)
            
            # Should have at least one strength and one area to improve
            self.assertTrue(len(feedback['strengths']) > 0)
            self.assertTrue(len(feedback['areas_to_improve']) > 0)
            
            # Suggestions should be a string
            self.assertTrue(isinstance(feedback['suggestions'], str))
        finally:
            # Restore the API key
            openai.api_key = original_key


class UrlsTest(TestCase):
    def setUp(self):
        self.client = Client()

    def test_home_url_resolves_to_index_view(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)

    def test_login_url_exists(self):
        response = self.client.get('/users/login/')
        self.assertEqual(response.status_code, 200)

    def test_register_url_exists(self):
        response = self.client.get('/users/register/')
        self.assertEqual(response.status_code, 200)

    def test_logout_url_redirects(self):
        response = self.client.get('/users/logout/')
        self.assertEqual(response.status_code, 302)

    def test_dashboard_url_exists(self):
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='StrongTestPass123'
        )
        self.client.login(username='testuser', password='StrongTestPass123')
        response = self.client.get('/dashboard/')
        self.assertEqual(response.status_code, 200)

    def test_interview_coach_url_exists(self):
        """Test that the interview coach URL exists and requires login"""
        response = self.client.get('/interview-coach/')
        self.assertEqual(response.status_code, 302)  # Should redirect to login

        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='StrongTestPass123'
        )
        self.client.login(username='testuser', password='StrongTestPass123')

        # Need to mock the interview questions generation
        with patch('home.interview_service.InterviewService.generate_interview_questions') as mock_gen:
            mock_gen.return_value = ["Test question 1", "Test question 2"]
            response = self.client.get('/interview-coach/')
            self.assertEqual(response.status_code, 200)


class StaticContentTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.home_url = reverse('index')

    def test_static_css_loaded(self):
        response = self.client.get(self.home_url)
        self.assertContains(response, '<link rel="stylesheet" href="')

    def test_font_awesome_loaded(self):
        response = self.client.get(self.home_url)
        self.assertContains(response, 'font-awesome')

    def test_page_contains_header(self):
        response = self.client.get(self.home_url)
        self.assertContains(response, '<header>')

    def test_page_contains_footer(self):
        response = self.client.get(self.home_url)
        self.assertContains(response, '<footer')
        self.assertContains(response, 'id="contact"')

    def test_page_contains_main_content(self):
        response = self.client.get(self.home_url)
        self.assertContains(response, '<main>')
        self.assertContains(response, 'id="features"')
        self.assertContains(response, 'id="how-it-works"')


class AuthRedirectTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.dashboard_url = reverse('dashboard')
        self.profile_url = reverse('profile')
        self.interview_coach_url = reverse('interview_coach')

        # Create a test user
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='StrongTestPass123'
        )

    def test_dashboard_redirects_to_login(self):
        """Test that dashboard redirects to login when user is not authenticated"""
        response = self.client.get(self.dashboard_url)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith('/users/login/'))
        self.assertTrue('next=/dashboard/' in response.url)

    def test_profile_redirects_to_login(self):
        """Test that profile redirects to login when user is not authenticated"""
        response = self.client.get(self.profile_url)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith('/users/login/'))
        self.assertTrue('next=/users/profile/' in response.url)

    def test_interview_coach_redirects_to_login(self):
        """Test that interview coach redirects to login when user is not authenticated"""
        response = self.client.get(self.interview_coach_url)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith('/users/login/'))
        self.assertTrue('next=/interview-coach/' in response.url)

    def test_dashboard_accessible_when_authenticated(self):
        """Test that dashboard is accessible when user is authenticated"""
        self.client.login(username='testuser', password='StrongTestPass123')
        response = self.client.get(self.dashboard_url)
        self.assertEqual(response.status_code, 200)

    def test_profile_accessible_when_authenticated(self):
        """Test that profile is accessible when user is authenticated"""
        self.client.login(username='testuser', password='StrongTestPass123')
        response = self.client.get(self.profile_url)
        self.assertEqual(response.status_code, 200)

    def test_interview_coach_accessible_when_authenticated(self):
        """Test that interview coach is accessible when user is authenticated"""
        self.client.login(username='testuser', password='StrongTestPass123')
        with patch('home.interview_service.InterviewService.generate_interview_questions') as mock_gen:
            mock_gen.return_value = ["Test question 1", "Test question 2"]
            response = self.client.get(self.interview_coach_url)
            self.assertEqual(response.status_code, 200)

    def test_login_redirect_to_next_url(self):
        """Test that after login, user is redirected to the 'next' URL"""
        response = self.client.get(self.dashboard_url)
        login_url = response.url  # This will be '/users/login/?next=/dashboard/'

        # Now login with this URL
        response = self.client.post(
            login_url,
            {'username': 'testuser', 'password': 'StrongTestPass123'},
            follow=True
        )

        # The first redirected URL should be to the dashboard
        self.assertEqual(response.redirect_chain[0][0], '/dashboard/')
        self.assertEqual(response.status_code, 200)
