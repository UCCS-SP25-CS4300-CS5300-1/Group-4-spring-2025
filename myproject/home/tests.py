from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from users.models import Profile
from home.models import Application, JobListing
from .forms import SearchJobForm, InterviewResponseForm, CoverLetterForm
from django.utils import timezone
from unittest.mock import patch, MagicMock
import os
import io


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

        # url with job id
        self.cover_letter_with_job_url = reverse('cover_letter_generator_with_job', args=[self.job.job_id])

        # sample resume content
        self.resume_content = b"bob smith\nSenior Python Developer\n5 years experience in Django development"

    def test_cover_letter_login_required(self):
        """testing that unauthenticated users are redirecting to login"""
        response = self.client.get(self.cover_letter_url)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith('/users/login/'))

    def test_cover_letter_with_job_login_required(self):
        """testing that unauthenticated users are redirecting when accessing cover letter with job"""
        response = self.client.get(self.cover_letter_with_job_url)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith('/users/login/'))

    def test_cover_letter_authenticated_user(self):
        """testing that authenticated users are accessing the cover letter generator"""
        self.client.login(username='testuser', password='StrongTestPass123')
        response = self.client.get(self.cover_letter_url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'home/cover_letter_generator.html')

        # Check for forms in context
        self.assertIsInstance(response.context['form'], CoverLetterForm)
        self.assertIsInstance(response.context['resume_form'], ResumeUploadForm)

    def test_cover_letter_with_job_authenticated_user(self):
        """testing that authenticated users are accessing the cover letter generator with a job"""
        self.client.login(username='testuser', password='StrongTestPass123')
        response = self.client.get(self.cover_letter_with_job_url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'home/cover_letter_generator.html')

        # checking that the job is in the context
        self.assertIn('job', response.context)
        self.assertEqual(response.context['job'], self.job)

        # verifying job details are pre-filling in form
        form = response.context['form']
        self.assertEqual(form.initial['company_name'], self.job.company)
        self.assertEqual(form.initial['job_title'], self.job.title)
        self.assertEqual(form.initial['job_description'], self.job.description)

    def test_form_validation_missing_fields(self):
        """testing validation when required fields are missing"""
        self.client.login(username='testuser', password='StrongTestPass123')

        # Submit form with missing fields
        response = self.client.post(self.cover_letter_url, {
            'applicant_name': 'John Doe',
            # Missing other required fields
        })

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'home/cover_letter_generator.html')
        self.assertTrue('form' in response.context)
        self.assertTrue(response.context['form'].errors)

        # Check for specific error messages
        form = response.context['form']
        self.assertIn('company_name', form.errors)
        self.assertIn('job_title', form.errors)

    def test_successful_cover_letter_generation(self):
        """testing successful cover letter generating and PDF response"""
        self.client.login(username='testuser', password='StrongTestPass123')

    
        with patch('home.cover_letter_service.CoverLetterService.generate_cover_letter') as mock_generate, \
         patch('home.cover_letter_service.CoverLetterService.create_cover_letter_pdf') as mock_create_pdf:
        
        mock_generate.return_value = "This is a generated cover letter content."
        mock_create_pdf.return_value = b"%PDF-1.4 mock pdf content"

        # submitting form with all required fields
        response = self.client.post(self.cover_letter_url, {
            'user_name': 'bob smith',
            'user_email': 'test@example.com',
            'user_phone': '1234567890',
            'user_address': '123 Test Street',
            'use_resume': False,
            'company_name': 'Test Company',
            'job_title': 'Python Developer',
            'job_description': 'Django development role',
        })

        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/pdf')
        self.assertIn('attachment; filename=', response['Content-Disposition'])
        self.assertTrue(response.content.startswith(b'%PDF'))

        
        mock_generate.assert_called_once()
        mock_create_pdf.assert_called_once_with(
            cover_letter_text="This is a generated cover letter content.",
            filename="cover_letter_testuser"
        )


    def test_pdf_generation_view(self):
        """testing the pdf generating view"""
        self.client.login(username='testuser', password='StrongTestPass123')

        # creating a session variable with cover letter content
        session = self.client.session
        session['cover_letter'] = "This is a cover letter that should be in the PDF."
        session.save()

        # Mock the PDF generation
        with patch('home.views.generate_pdf') as mock_pdf:
            # Create a mock PDF file
            mock_pdf_content = b"%PDF-1.4 mock pdf content"
            mock_pdf.return_value = mock_pdf_content

            response = self.client.get(reverse('download_cover_letter'))

            # checking response properties
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response['Content-Type'], 'application/pdf')
            self.assertEqual(response['Content-Disposition'], 'attachment; filename="cover_letter.pdf"')

            # Check content
            self.assertEqual(response.content, mock_pdf_content)

            # Verify mock was called with correct content
            mock_pdf.assert_called_once_with("This is a cover letter that should be in the PDF.")

    def test_pdf_generation_no_content(self):
        """testing pdf generating when no cover letter content is available"""
        self.client.login(username='testuser', password='StrongTestPass123')

        # No cover letter in session
        response = self.client.get(reverse('download_cover_letter'))

        # Should redirect to cover letter generator
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('cover_letter_generator'))

    def test_resume_upload_and_extraction(self):
        """testing resume uploading and text extracting"""
        self.client.login(username='testuser', password='StrongTestPass123')

        # Create a mock PDF file
        resume_file = SimpleUploadedFile(
            "resume.pdf",
            self.resume_content,
            content_type="application/pdf"
        )

        # Mock the resume text extraction
        with patch('home.views.extract_text_from_pdf') as mock_extract:
            mock_extract.return_value = "John Doe\nSenior Python Developer\n5 years experience in Django"

            response = self.client.post(
                self.cover_letter_url,
                {
                    'resume_file': resume_file,
                },
                format='multipart'
            )

            self.assertEqual(response.status_code, 200)
            self.assertTemplateUsed(response, 'home/cover_letter_generator.html')

            # checking that extracted text is in the form
            form = response.context['form']
            self.assertIn('bob smith', form.initial['applicant_name'])
            self.assertIn('Python Developer', form.initial['skills'])

            # Verify mock was called
            mock_extract.assert_called_once()

    def test_resume_upload_invalid_file(self):
        """testing resume uploading with invalid file type"""
        self.client.login(username='testuser', password='StrongTestPass123')

        # Create a non-PDF file
        invalid_file = SimpleUploadedFile(
            "resume.txt",
            b"This is not a PDF file",
            content_type="text/plain"
        )

        response = self.client.post(
            self.cover_letter_url,
            {
                'resume_file': invalid_file,
            },
            format='multipart'
        )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'home/cover_letter_generator.html')

        # Check for error in resume form
        self.assertTrue('resume_form' in response.context)
        self.assertTrue(response.context['resume_form'].errors)
        self.assertIn('resume_file', response.context['resume_form'].errors)

    def test_dashboard_integration(self):
        """testing that the dashboard is containing links to the cover letter generator"""
        self.client.login(username='testuser', password='StrongTestPass123')

        # Mock the JobicyService.search_jobs method to return our test job
        with patch('home.services.JobicyService.search_jobs') as mock_search:
            mock_search.return_value = [self.job]

            response = self.client.post(reverse('dashboard'), {'search_term': 'python'})

            # Check that the cover letter generator link is in the response
            self.assertContains(response, 'Generate Cover Letter')
            self.assertContains(response, f'/cover-letter/{self.job.job_id}/')


class CoverLetterServiceTest(TestCase):
    """Tests for the CoverLetterService class"""

    def test_generate_cover_letter_fallback(self):
        """testing that generate_cover_letter is returning fallback content when api is failing"""
        from home.cover_letter_service import CoverLetterService

        # Force API failure by making openai.api_key None temporarily
        import openai
        original_key = openai.api_key
        openai.api_key = None

        try:
            # This should use fallback content
            cover_letter = CoverLetterService.generate_cover_letter(
                "bob smith",
                "ACME Corp",
                "Software Engineer",
                "Python development role",
                "Python, Django, API development",
                "5 years of web development"
            )

            # verifying we got some cover letter content
            self.assertTrue(len(cover_letter) > 0)
            self.assertTrue(isinstance(cover_letter, str))

            # verifying that the content is including the provided information
            self.assertIn("bob smith", cover_letter)
            self.assertIn("ACME Corp", cover_letter)
            self.assertIn("Software Engineer", cover_letter)
        finally:
            # Restore the API key
            openai.api_key = original_key

    def test_generate_pdf(self):
        """testing the pdf generating function"""
        from home.cover_letter_service import generate_pdf

        # Mock the reportlab functionality
        with patch('home.cover_letter_service.SimpleDocTemplate') as mock_doc:
            mock_instance = MagicMock()
            mock_doc.return_value = mock_instance

            result = generate_pdf("This is test content for the PDF")

            # Verify the mock was called
            mock_doc.assert_called_once()
            mock_instance.build.assert_called_once()

    def test_extract_text_from_pdf(self):
        """testing the pdf text extracting function"""
        from home.cover_letter_service import extract_text_from_pdf

        # Create a temporary PDF file
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_file:
            temp_file.write(b"%PDF-1.4 mock pdf content")
            temp_file_path = temp_file.name

        try:
            # Mock PyPDF2 functionality
            with patch('home.cover_letter_service.PdfReader') as mock_reader:
                mock_reader_instance = MagicMock()
                mock_reader.return_value = mock_reader_instance

                # setting up the mock to returning text
                mock_page = MagicMock()
                mock_page.extract_text.return_value = "bob smith\nSenior Developer\n"
                mock_reader_instance.pages = [mock_page, mock_page]  # Two pages

                result = extract_text_from_pdf(temp_file_path)

                # checking results
                self.assertEqual(result, "bob smith\nSenior Developer\nbob smith\nSenior Developer\n")
                mock_reader.assert_called_once_with(temp_file_path)
        finally:
            # Clean up the temp file
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)


class UrlsTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='StrongTestPass123'
        )

        # Create a test job listing
        self.job = JobListing.objects.create(
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

    def test_cover_letter_url_exists(self):
        """testing that the cover letter url is existing and requiring login"""
        response = self.client.get('/cover-letter/')
        self.assertEqual(response.status_code, 302)  # Should redirect to login

        self.client.login(username='testuser', password='StrongTestPass123')
        response = self.client.get('/cover-letter/')
        self.assertEqual(response.status_code, 200)

    def test_cover_letter_with_job_url_exists(self):
        """testing that the cover letter with job url is existing and requiring login"""
        response = self.client.get(f'/cover-letter/{self.job.job_id}/')
        self.assertEqual(response.status_code, 302)  # Should redirect to login

        self.client.login(username='testuser', password='StrongTestPass123')
        response = self.client.get(f'/cover-letter/{self.job.job_id}/')
        self.assertEqual(response.status_code, 200)

    def test_download_cover_letter_url_exists(self):
        """testing that the download cover letter url is existing and requiring login"""
        response = self.client.get('/cover-letter/download/')
        self.assertEqual(response.status_code, 302)  # Should redirect to login

        self.client.login(username='testuser', password='StrongTestPass123')

        # Create a session variable with cover letter content
        session = self.client.session
        session['cover_letter'] = "This is a test cover letter."
        session.save()

        # Mock PDF generation
        with patch('home.views.generate_pdf') as mock_pdf:
            mock_pdf.return_value = b"%PDF-1.4 mock pdf content"
            response = self.client.get('/cover-letter/download/')
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response['Content-Type'], 'application/pdf')


class CoverLetterFormTest(TestCase):
    """Tests for the cover letter form"""

    def test_form_valid_data(self):
        """testing form with valid data"""
        from home.forms import CoverLetterForm

        form_data = {
            'applicant_name': 'John Doe',
            'company_name': 'ACME Corp',
            'job_title': 'Software Engineer',
            'job_description': 'Python development role',
            'skills': 'Python, Django, API development',
            'experience': '5 years of web development',
        }

        form = CoverLetterForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_form_invalid_data(self):
        """testing form with invalid data"""
        from home.forms import CoverLetterForm

        # Missing required fields
        form_data = {
            'applicant_name': 'John Doe',
            # Missing other fields
        }

        form = CoverLetterForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('company_name', form.errors)
        self.assertIn('job_title', form.errors)

    def test_form_max_length(self):
        """testing form field max length validating"""
        from home.forms import CoverLetterForm

        # Create strings that exceed max length
        long_name = 'A' * 101  # Assuming max_length=100
        long_description = 'A' * 2001  # Assuming max_length=2000

        form_data = {
            'applicant_name': long_name,
            'company_name': 'ACME Corp',
            'job_title': 'Software Engineer',
            'job_description': long_description,
            'skills': 'Python, Django',
            'experience': '5 years',
        }

        form = CoverLetterForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('applicant_name', form.errors)
        self.assertIn('job_description', form.errors)
