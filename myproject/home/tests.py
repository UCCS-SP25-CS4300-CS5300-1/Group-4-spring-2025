from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from users.models import Profile
from home.models import JobListing
from .forms import SearchJobForm, CoverLetterForm
from django.utils import timezone
from unittest.mock import patch, MagicMock
from users.models import Resume
from django.core.files.uploadedfile import SimpleUploadedFile
from django.http import HttpResponse
from home.models import UserJobInteraction

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
        self.assertContains(response, 'Search for Jobs')
        self.assertContains(response, 'href="/dashboard/"')

        self.assertNotContains(response, 'class="login-btn"')

    def test_home_view_unauthenticated_user(self):
        response = self.client.get(self.home_url)

        self.assertContains(response, 'Login')
        self.assertContains(response, 'Sign Up')
        self.assertContains(response, 'Sign Up')

        self.assertNotContains(response, 'Hello, testuser')
        self.assertNotContains(response, 'Search for Jobs')


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
        self.client.login(username='testuser', password='StrongTestPass123')
        response = self.client.get(self.interview_coach_url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'home/interview_coach.html')

        self.assertIn('questions', response.context)
        self.assertEqual(len(response.context['questions']), 0)
        self.assertEqual(response.context['questions'], [])
        self.assertIsNone(response.context.get('job'))
        self.assertEqual(response.context.get('job_description'), "")

    def test_interview_coach_with_job_authenticated_user(self):
        """Test that authenticated users can access the interview coach with a job (initial load)"""
        self.client.login(username='testuser', password='StrongTestPass123')
        response = self.client.get(self.interview_coach_with_job_url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'home/interview_coach.html')

        self.assertIn('questions', response.context)
        self.assertEqual(len(response.context['questions']), 0)
        self.assertEqual(response.context['questions'], [])
        self.assertEqual(response.context.get('job'), self.job)
        self.assertEqual(response.context.get('job_description'), self.job.description)

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

    def test_ajax_generate_questions(self):
        """Test the API endpoint for generating questions asynchronously."""
        self.client.login(username='testuser', password='StrongTestPass123')
        generate_url = reverse('generate_questions')

        with patch('home.interview_service.InterviewService.generate_interview_questions') as mock_generate:
            mock_generate.return_value = ["Generic Q1", "Generic Q2"]
            response = self.client.post(generate_url, {}, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
            
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json(), {'questions': ["Generic Q1", "Generic Q2"]})
            mock_generate.assert_called_once_with("") 

        with patch('home.interview_service.InterviewService.generate_interview_questions') as mock_generate:
            mock_generate.return_value = ["Job Q1", "Job Q2"]
            response = self.client.post(generate_url, {'job_description': self.job.description}, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
            
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json(), {'questions': ["Job Q1", "Job Q2"]})
            mock_generate.assert_called_once_with(self.job.description)
            
    def test_ajax_generate_questions_error(self):
        """Test error handling in the question generation API."""
        self.client.login(username='testuser', password='StrongTestPass123')
        generate_url = reverse('generate_questions')

        with patch('home.interview_service.InterviewService.generate_interview_questions') as mock_generate:
            mock_generate.side_effect = Exception("AI Service Down") # Simulate an error
            response = self.client.post(generate_url, {}, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
            
            self.assertEqual(response.status_code, 500)
            self.assertEqual(response.json(), {'error': 'Failed to generate questions. Please try again.'})


class InterviewServiceTest(TestCase):
    """tests for the InterviewService class"""

    @patch('home.interview_service.InterviewService.get_api_key', return_value=None)
    def test_generate_interview_questions_fallback(self, mock_get_key):
        """Test that generate_interview_questions returns fallback questions when API key is not found"""
        from home.interview_service import InterviewService
        

        questions = InterviewService.generate_interview_questions("Test job description")
        
        self.assertTrue(len(questions) > 0)
        self.assertTrue(isinstance(questions, list))
        self.assertTrue(all(isinstance(q, str) for q in questions))
        

        self.assertIn("Tell me about yourself and why you're interested in this position.", questions[0])


    @patch('home.interview_service.InterviewService.get_api_key', return_value=None)
    def test_evaluate_response_fallback(self, mock_get_key):
        """Test that evaluate_response returns fallback feedback when API key is not found"""
        from home.interview_service import InterviewService
        

        feedback = InterviewService.evaluate_response(
            "Tell me about yourself.",
            "I am a Python developer with 5 years of experience.",
            "Python Developer job description"
        )
        
        self.assertIn('score', feedback)
        self.assertIn('strengths', feedback)
        self.assertIn('areas_to_improve', feedback)
        self.assertIn('suggestions', feedback)
        
        self.assertTrue(1 <= feedback['score'] <= 10)
        
        self.assertTrue(len(feedback['strengths']) > 0)
        self.assertTrue(len(feedback['areas_to_improve']) > 0)
        
        self.assertTrue(isinstance(feedback['suggestions'], str))


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


class CoverLetterGeneratorViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.cover_letter_url = reverse('cover_letter_generator')

        # Creating a test user
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='StrongTestPass123'
        )

        self.profile = Profile.objects.get(user=self.user)
        self.profile.save()

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

        self.cover_letter_with_job_url = reverse('cover_letter_generator_with_job', args=[self.job.job_id])
        self.resume_content = b"bob smith\nSenior Python Developer\n5 years experience in Django development"

    def test_cover_letter_login_required(self):
        response = self.client.get(self.cover_letter_url)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith('/users/login/'))

    def test_cover_letter_with_job_login_required(self):
        response = self.client.get(self.cover_letter_with_job_url)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith('/users/login/'))

    def test_cover_letter_authenticated_user(self):
        self.client.login(username='testuser', password='StrongTestPass123')
        response = self.client.get(self.cover_letter_url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'home/cover_letter_generator.html')
        self.assertIsInstance(response.context['form'], CoverLetterForm)

    def test_cover_letter_with_job_authenticated_user(self):
        self.client.login(username='testuser', password='StrongTestPass123')
        response = self.client.get(self.cover_letter_with_job_url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'home/cover_letter_generator.html')
        self.assertIn('job', response.context)
        self.assertEqual(response.context['job'], self.job)

        form = response.context['form']
        self.assertEqual(form.initial['company_name'], self.job.company)
        self.assertEqual(form.initial['job_title'], self.job.title)
        self.assertEqual(form.initial['job_description'], self.job.description)

    def test_successful_cover_letter_generation(self):
        self.client.login(username='testuser', password='StrongTestPass123')

        with patch('home.cover_letter_service.CoverLetterService.generate_cover_letter') as mock_generate, \
             patch('home.cover_letter_service.CoverLetterService.create_cover_letter_pdf') as mock_create_pdf:

            mock_generate.return_value = "This is a generated cover letter content."
            mock_create_pdf.return_value = b"%PDF-1.4 mock pdf content"

            response = self.client.post(self.cover_letter_url, {
                'user_name': 'bob smith',
                'user_email': 'test@example.com',
                'user_phone': '1234567890',
                'user_address': '123 Test Street',
                'use_resume': False,
                'company_name': 'Test Company',
                'job_title': 'Python Developer',
                'job_description': 'Django development role',
            }, HTTP_USER_AGENT='Mozilla/5.0 Python-tests')

            self.assertEqual(response.status_code, 200)
            self.assertEqual(response['Content-Type'], 'application/pdf')
            self.assertIn('attachment; filename=', response['Content-Disposition'])
            self.assertTrue(response.content.startswith(b'%PDF'))

            mock_generate.assert_called_once()
            mock_create_pdf.assert_called_once_with(
                cover_letter_text="This is a generated cover letter content.",
                filename="cover_letter_testuser"
            )
    def test_generate_cover_letter_api_error(self):
        from home.cover_letter_service import CoverLetterService

        with patch('home.cover_letter_service.requests.post') as mock_post, \
             patch.object(CoverLetterService, 'get_api_key', return_value='fake-key'):

            mock_post.return_value.status_code = 500
            mock_post.return_value.text = 'Internal Server Error'

            result = CoverLetterService.generate_cover_letter(
            job_description="Test job",
            user_info={"name": "Jane Doe"}
            )

            self.assertIn("Dear Hiring Manager", result)  # fallback letter
    def test_generate_cover_letter_api_exception(self):
        from home.cover_letter_service import CoverLetterService

        with patch('home.cover_letter_service.requests.post', side_effect=Exception("Connection error")), \
             patch.object(CoverLetterService, 'get_api_key', return_value='fake-key'):

            result = CoverLetterService.generate_cover_letter(
                job_description="Test job",
                user_info={"name": "Jane Doe"}
            )

            self.assertIn("Dear Hiring Manager", result)  # fallback letter


    def test_template_cover_letter_content(self):
        from home.cover_letter_service import CoverLetterService

        user_info = {
            "name": "Alice Smith",
            "email": "alice@example.com",
            "phone": "555-1234",
            "address": "123 Main St"
        }
        date = "April 15, 2025"

        result = CoverLetterService._get_template_cover_letter(user_info, date)

        self.assertIn("Alice Smith", result)
        self.assertIn("April 15, 2025", result)
        self.assertIn("[Company Name]", result)
        self.assertIn("[Position Title]", result)
    def test_create_pdf_with_blank_content(self):
        from home.cover_letter_service import CoverLetterService

        result = CoverLetterService.create_cover_letter_pdf("\n\n\n", "blank_letter")
        self.assertTrue(result.startswith(b'%PDF'))
        self.assertGreater(len(result), 100)
    def test_extract_text_from_resume_error(self):
        from home.cover_letter_service import CoverLetterService

        mock_file = MagicMock()
        with patch('home.cover_letter_service.PdfReader', side_effect=Exception("boom!")):
            result = CoverLetterService.extract_text_from_resume(mock_file)
            self.assertIsNone(result)


class ResumeFeedbackTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='StrongTestPass123'
        )
        self.profile = Profile.objects.get(user=self.user)
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
        self.resume_content = b"Bob Smith\nSenior Python Developer\n5 years experience in Python, Django"
        self.resume = Resume.objects.create(
            user=self.user,
            resume=SimpleUploadedFile("resume.pdf", self.resume_content)
        )
        self.apply_flow_url = reverse('apply_flow', args=[self.job.job_id])
        self.resume_feedback_url = reverse('resume_feedback')

    def test_apply_flow_with_resume(self):
        self.client.login(username='testuser', password='StrongTestPass123')
        
        with patch('home.views.JobicyService.get_job_details') as mock_get_job_details, \
             patch('users.views.parse_resume', return_value="Parsed resume content"):
            
            mock_get_job_details.return_value = self.job
            
            response = self.client.get(self.apply_flow_url)
            self.assertEqual(response.status_code, 200)
            self.assertTemplateUsed(response, 'home/apply_flow.html')
            self.assertTrue('resume_text' in response.context)
            self.assertEqual(response.context['resume_text'], "Parsed resume content")
            
            self.assertContains(response, 'Get Resume Feedback')
            self.assertContains(response, f'formData.append(\'resume_id\', \'{self.resume.id}\')')

    def test_ajax_resume_feedback_success(self):
        self.client.login(username='testuser', password='StrongTestPass123')
        
        with patch('users.views.parse_resume', return_value="Parsed resume content"), \
             patch('users.views.get_resume_feedback', return_value="General resume feedback"), \
             patch('home.views.get_job_specific_feedback', return_value="Job-specific feedback"):
            
            response = self.client.post(
                self.resume_feedback_url,
                {
                    'resume_id': self.resume.id,
                    'job_description': self.job.description
                },
                HTTP_X_REQUESTED_WITH='XMLHttpRequest'
            )
            
            self.assertEqual(response.status_code, 200)
            data = response.json()
            self.assertTrue(data['success'])
            self.assertEqual(data['general_feedback'], "General resume feedback")
            self.assertEqual(data['job_specific_feedback'], "Job-specific feedback")

    def test_ajax_resume_feedback_no_resume(self):
        self.client.login(username='testuser', password='StrongTestPass123')
        
        response = self.client.post(
            self.resume_feedback_url,
            {
                'job_description': self.job.description
            },
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertEqual(data['error'], 'No resume selected')

    def test_ajax_resume_feedback_invalid_resume(self):
        self.client.login(username='testuser', password='StrongTestPass123')
        
        response = self.client.post(
            self.resume_feedback_url,
            {
                'resume_id': 9999,
                'job_description': self.job.description
            },
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        
        self.assertEqual(response.status_code, 404)
        data = response.json()
        self.assertEqual(data['error'], 'Resume not found')

    def test_ajax_resume_feedback_not_ajax(self):
        self.client.login(username='testuser', password='StrongTestPass123')
        
        response = self.client.post(
            self.resume_feedback_url,
            {
                'resume_id': self.resume.id,
                'job_description': self.job.description
            }
        )
        
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertEqual(data['error'], 'Invalid request')

    def test_get_job_specific_feedback(self):
        from home.views import get_job_specific_feedback
        
        with patch('openai.chat.completions.create') as mock_openai:
            mock_openai.return_value.choices = [MagicMock(message=MagicMock(content="Mocked feedback"))]
            
            result = get_job_specific_feedback("Resume text", "Job description")
            self.assertEqual(result, "Mocked feedback")
            
            mock_openai.assert_called_once()
            call_args = mock_openai.call_args[1]
            self.assertEqual(call_args['model'], "gpt-4o-mini")
            self.assertEqual(len(call_args['messages']), 2)
            self.assertIn("Resume", call_args['messages'][1]['content'])
            self.assertIn("Job Description", call_args['messages'][1]['content'])
            
        with patch('os.environ.get', return_value=None):
            result = get_job_specific_feedback("Resume text", "Job description")
            self.assertIn("requires an OpenAI API key", result)
        
        with patch('openai.chat.completions.create', side_effect=Exception("API error")):
            result = get_job_specific_feedback("Resume text", "Job description")
            self.assertIn("Unable to generate job-specific feedback", result)
            self.assertIn("API error", result)


class ApplyFlowViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='StrongTestPass123'
        )
        self.profile = Profile.objects.get(user=self.user)
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
        self.resume_content = b"Bob Smith\nSenior Python Developer\n5 years experience in Python, Django"
        self.resume = Resume.objects.create(
            user=self.user,
            resume=SimpleUploadedFile("resume.pdf", self.resume_content)
        )
        self.apply_flow_url = reverse('apply_flow', args=[self.job.job_id])

    def test_apply_flow_login_required(self):
        response = self.client.get(self.apply_flow_url)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith('/users/login/'))

    def test_apply_flow_authenticated_user(self):
        self.client.login(username='testuser', password='StrongTestPass123')
        
        with patch('home.views.JobicyService.get_job_details') as mock_get_job_details:
            mock_get_job_details.return_value = self.job
            
            response = self.client.get(self.apply_flow_url)
            self.assertEqual(response.status_code, 200)
            self.assertTemplateUsed(response, 'home/apply_flow.html')
            
            self.assertEqual(response.context['job'], self.job)
            self.assertEqual(response.context['latest_resume'], self.resume)
            self.assertTrue(response.context['has_resume'])
            
            form = response.context['form']
            self.assertEqual(form.initial['job_description'], self.job.description)
            self.assertEqual(form.initial['company_name'], self.job.company)
            self.assertEqual(form.initial['job_title'], self.job.title)
            self.assertEqual(form.initial['user_name'], 'testuser')
            self.assertEqual(form.initial['use_resume'], True)

    def test_apply_flow_invalid_job_id(self):
        self.client.login(username='testuser', password='StrongTestPass123')
        
        with patch('home.views.JobicyService.get_job_details', return_value=None), \
             patch('home.views.render') as mock_render:
            
            mock_render.return_value = HttpResponse(status=200)
            
            invalid_url = reverse('apply_flow', args=['invalid-job-id'])
            response = self.client.get(invalid_url)
            
            mock_render.assert_called_once()
            args, kwargs = mock_render.call_args
            self.assertEqual(args[1], 'home/apply_flow_error.html')
            self.assertEqual(args[2]['job_id'], 'invalid-job-id')

    def test_apply_flow_with_resume_error(self):
        self.client.login(username='testuser', password='StrongTestPass123')
        
        with patch('home.views.JobicyService.get_job_details') as mock_get_job_details, \
             patch('users.views.parse_resume', side_effect=Exception("Resume parsing error")):
            
            mock_get_job_details.return_value = self.job
            
            response = self.client.get(self.apply_flow_url)
            self.assertEqual(response.status_code, 200)
            
            messages = list(response.context['messages'])
            self.assertTrue(any("Error extracting text from your resume" in str(m) for m in messages))
            self.assertIsNone(response.context['resume_text'])

    def test_job_outlook_success(self):
        self.client.login(username='testuser', password='StrongTestPass123')
        
        with patch('home.views.get_job_fit_analysis', return_value="Sample job fit analysis"), \
             patch('users.views.parse_resume', return_value="Resume content"):
            
            response = self.client.post(
                reverse('job_outlook'),
                {
                    'job_title': 'Python Developer',
                    'job_description': 'Sample job description',
                    'industry': 'Technology',
                    'location': 'Remote'
                },
                HTTP_X_REQUESTED_WITH='XMLHttpRequest'
            )
            
            self.assertEqual(response.status_code, 200)
            data = response.json()
            self.assertTrue(data['success'])
            self.assertEqual(data['fit_analysis'], "Sample job fit analysis")

    def test_job_outlook_missing_title(self):
        self.client.login(username='testuser', password='StrongTestPass123')
        
        response = self.client.post(
            reverse('job_outlook'),
            {
                'job_description': 'Sample job description',
                'industry': 'Technology',
                'location': 'Remote'
            },
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertEqual(data['error'], 'No job title provided')

    def test_job_outlook_with_resume(self):
        self.client.login(username='testuser', password='StrongTestPass123')
        
        with patch('users.views.parse_resume', return_value="Resume content"), \
             patch('home.views.get_job_fit_analysis') as mock_analysis:
            
            mock_analysis.return_value = "Analysis with resume data"
            
            response = self.client.post(
                reverse('job_outlook'),
                {
                    'job_title': 'Python Developer',
                    'job_description': 'Sample job description',
                },
                HTTP_X_REQUESTED_WITH='XMLHttpRequest'
            )
            
            self.assertEqual(response.status_code, 200)
            call_args = mock_analysis.call_args[1]
            self.assertEqual(call_args['resume_text'], "Resume content")
            self.assertEqual(call_args['job_title'], "Python Developer")

    def test_rejection_simulator_success(self):
        self.client.login(username='testuser', password='StrongTestPass123')
        
        with patch('home.views.generate_rejection_reasons', return_value="Sample rejection reasons"), \
             patch('users.views.parse_resume', return_value="Resume content"):
            
            response = self.client.post(
                reverse('rejection_generator'),
                {
                    'job_title': 'Python Developer',
                    'job_description': 'Sample job description',
                    'industry': 'Technology',
                    'location': 'Remote'
                },
                HTTP_X_REQUESTED_WITH='XMLHttpRequest'
            )
            
            self.assertEqual(response.status_code, 200)
            data = response.json()
            self.assertTrue(data['success'])
            self.assertEqual(data['rejection_reasons'], "Sample rejection reasons")        

    def test_rejection_simulator_missing_title(self):
        self.client.login(username='testuser', password='StrongTestPass123')
        
        response = self.client.post(
            reverse('rejection_generator'),
            {
                'job_description': 'Sample job description',
                'industry': 'Technology',
                'location': 'Remote'
            },
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertEqual(data['error'], 'No job title provided')      

    def test_rejection_simulator_with_resume(self):
        self.client.login(username='testuser', password='StrongTestPass123')
        
        with patch('users.views.parse_resume', return_value="Resume content"), \
             patch('home.views.generate_rejection_reasons') as mock_analysis:
            
            mock_analysis.return_value = "Analysis with resume data"
            
            response = self.client.post(
                reverse('rejection_generator'),
                {
                    'job_title': 'Python Developer',
                    'job_description': 'Sample job description',
                },
                HTTP_X_REQUESTED_WITH='XMLHttpRequest'
            )
            
            self.assertEqual(response.status_code, 200)
            call_args = mock_analysis.call_args[1]
            self.assertEqual(call_args['resume_text'], "Resume content")
            self.assertEqual(call_args['job_title'], "Python Developer")   

    def test_rejection_simulator_with_no_resume(self):
        self.client.login(username='testuser', password='StrongTestPass123')
        
        with patch('users.views.parse_resume', return_value=None), \
             patch('home.views.generate_rejection_reasons') as mock_analysis:
            
            mock_analysis.return_value = "Analysis without resume data"
            
            response = self.client.post(
                reverse('rejection_generator'),
                {
                    'job_title': 'Python Developer',
                    'job_description': 'Sample job description',
                },
                HTTP_X_REQUESTED_WITH='XMLHttpRequest'
            )
            
            self.assertEqual(response.status_code, 200)
            call_args = mock_analysis.call_args[1]
            self.assertEqual(call_args['resume_text'], None)
            self.assertEqual(call_args['job_title'], "Python Developer")               

class JobTrackingTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser', 
            password='StrongTestPass123'
        )
        self.job1 = JobListing.objects.create(
            job_id='track-job-1', 
            title='Job 1', 
            company='Company A'
        )
        self.job2 = JobListing.objects.create(
            job_id='track-job-2', 
            title='Job 2', 
            company='Company B'
        )
        self.track_view_url = reverse('track_job_view')
        self.track_apply_url = reverse('track_application')
        self.applications_url = reverse('applications')
        self.client.login(username='testuser', password='StrongTestPass123')

    def test_track_job_view_success(self):
        response = self.client.post(
            self.track_view_url, 
            {'job_id': self.job1.job_id}, 
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertTrue(data['created'])
        self.assertTrue(UserJobInteraction.objects.filter(
            user=self.user, 
            job=self.job1, 
            interaction_type='viewed'
        ).exists())

    def test_track_job_view_twice(self):
        self.client.post(self.track_view_url, {'job_id': self.job1.job_id}, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        response = self.client.post(
            self.track_view_url, 
            {'job_id': self.job1.job_id}, 
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertFalse(data['created'])
        self.assertEqual(UserJobInteraction.objects.filter(user=self.user, job=self.job1, interaction_type='viewed').count(), 1)

    def test_track_job_view_invalid_job(self):
        response = self.client.post(
            self.track_view_url, 
            {'job_id': 'invalid-job-id'}, 
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        self.assertEqual(response.status_code, 404)

    def test_track_application_success(self):
        response = self.client.post(
            self.track_apply_url, 
            {'job_id': self.job1.job_id}, 
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertTrue(data['created'])
        self.assertTrue(UserJobInteraction.objects.filter(user=self.user, job=self.job1, interaction_type='applied').exists())
        self.assertTrue(UserJobInteraction.objects.filter(user=self.user, job=self.job1, interaction_type='viewed').exists())

    def test_applications_view_shows_tracked_jobs(self):
        self.client.post(self.track_view_url, {'job_id': self.job1.job_id}, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.client.post(self.track_apply_url, {'job_id': self.job2.job_id}, HTTP_X_REQUESTED_WITH='XMLHttpRequest')

        response = self.client.get(self.applications_url)
        self.assertEqual(response.status_code, 200)
        
        self.assertIn(self.job2, response.context['applied_jobs_list'])
        self.assertNotIn(self.job1, response.context['applied_jobs_list'])
        
        self.assertIn(self.job1, response.context['viewed_jobs_list'])
        self.assertNotIn(self.job2, response.context['viewed_jobs_list'], "Applied job should not appear in the viewed list.")
