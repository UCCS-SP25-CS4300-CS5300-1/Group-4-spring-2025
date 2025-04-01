from io import StringIO
from django.core.management import call_command
from django.test import TestCase
from django.contrib.auth.models import User
from users.models import Profile

class CreateAdminTeamTest(TestCase):
    def setUp(self):
        self.existing_user = User.objects.create_user(
            username='existinguser',
            email='existing@example.com',
            password='ExistingPass123'
        )

    def test_create_admin_team_command_with_args(self):
        out = StringIO()
        
        call_command(
            'create_admin_team',
            emails=['existing@example.com', 'new@example.com'],
            stdout=out
        )
        output = out.getvalue()

        self.existing_user.refresh_from_db()
        self.assertTrue(self.existing_user.is_superuser)
        self.assertTrue(self.existing_user.is_staff)
        self.assertIn('Made existing user existing@example.com a superuser', output)

        new_user = User.objects.get(email='new@example.com')
        self.assertTrue(new_user.is_superuser)
        self.assertTrue(new_user.is_staff)
        self.assertTrue(new_user.check_password('ChangeMe123!'))
        self.assertTrue(hasattr(new_user, 'profile'))
        self.assertIn('Created new superuser new@example.com', output)

    def test_create_admin_team_command_no_emails(self):
        """Test that running the command with no emails shows warning"""
        out = StringIO()
        call_command('create_admin_team', stdout=out)
        output = out.getvalue()
        self.assertIn('No emails provided and no default emails set', output)

    def test_create_admin_team_idempotent(self):
        """Test that running the command multiple times doesn't cause issues"""
        out = StringIO()
        
        call_command(
            'create_admin_team',
            emails=['existing@example.com'],
            stdout=out
        )
        call_command(
            'create_admin_team',
            emails=['existing@example.com'],
            stdout=out
        )

        ### BORING
        output = out.getvalue()

        self.existing_user.refresh_from_db()
        self.assertTrue(self.existing_user.is_superuser)
        self.assertTrue(self.existing_user.is_staff)
        self.assertEqual(User.objects.filter(email='existing@example.com').count(), 1)

    def tearDown(self):
        User.objects.all().delete()
        Profile.objects.all().delete() 