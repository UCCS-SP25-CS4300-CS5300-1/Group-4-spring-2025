from io import StringIO
from django.test import TestCase
from django.core.management import call_command
from django.contrib.auth.models import User
from users.management.commands.create_admin_team import Command
from unittest.mock import patch, MagicMock

class CreateAdminTeamTest(TestCase):
    def setUp(self):
        self.existing_user = User.objects.create_user(
            username='testuser',
            email='testuser@example.com',
            password='password123'
        )
        
        self.non_admin_user = User.objects.create_user(
            username='regularuser',
            email='regular@example.com',
            password='password123'
        )
        
        self.existing_superuser = User.objects.create_superuser(
            username='adminuser',
            email='admin@example.com',
            password='password123'
        )
        
        self.command = Command()
        self.team_emails = self.command.team_emails
    
    def test_command_creates_team_members(self):
        """Test that the command creates admin users for team members"""
        out = StringIO()
        
        call_command('create_admin_team', stdout=out)
        output = out.getvalue()
        
        self.assertIn('Skipping existing superuser admin@example.com', output)
        
        for email in self.team_emails:
            username = email.split('@')[0]
            try:
                user = User.objects.get(email=email)
                self.assertTrue(user.is_superuser)
                self.assertTrue(user.is_staff)
            
                if(user != self.existing_superuser):
                    self.assertTrue(
                        f'Created new superuser {email}' in output or 
                        f'Made existing user {email} a superuser' in output,
                        f"Expected creation/upgrade message for {email} not found in output"
                    )
            except User.DoesNotExist:
                self.fail(f"User with email {email} was not created")
    
    def test_command_with_specific_emails(self):
        """Test command with specific emails passed as arguments"""
        out = StringIO()
        test_emails = ['newadmin1@example.com', 'newadmin2@example.com', 'testuser@example.com']
        
        call_command('create_admin_team', '--emails', *test_emails, stdout=out)
        output = out.getvalue()
        
        for email in test_emails:
            if(email == 'testuser@example.com'):
                self.assertIn('Made existing user testuser@example.com a superuser', output)
            else:
                self.assertIn(f'Created new superuser {email}', output)
        
        for email in test_emails:
            user = User.objects.get(email=email)
            self.assertTrue(user.is_superuser)
            self.assertTrue(user.is_staff)
        
        self.non_admin_user.refresh_from_db()
        self.assertFalse(self.non_admin_user.is_superuser)
    
    def test_command_with_no_emails(self):
        """Test command when no emails are provided and team_emails is empty"""
        original_init = Command.__init__
        
        def mock_init(self, *args, **kwargs):
            original_init(self, *args, **kwargs)
            self.team_emails = []
            
        with patch.object(Command, '__init__', mock_init):
            out = StringIO()
            call_command('create_admin_team', stdout=out)
            output = out.getvalue()
            
            self.assertIn('No emails provided and no default emails set', output)
    
    def test_existing_user_upgraded(self):
        """Test that existing non-superuser users are upgraded"""
        out = StringIO()
        
        self.assertFalse(self.existing_user.is_superuser)
        self.assertFalse(self.existing_user.is_staff)
        
        call_command('create_admin_team', '--emails', 'testuser@example.com', stdout=out)
        output = out.getvalue()
        
        self.assertIn('Made existing user testuser@example.com a superuser', output)
        
        self.existing_user.refresh_from_db()
        self.assertTrue(self.existing_user.is_superuser)
        self.assertTrue(self.existing_user.is_staff)
    
    def test_superuser_not_modified(self):
        """Test that existing superusers are not modified"""
        out = StringIO()
        
        call_command('create_admin_team', '--emails', 'admin@example.com', stdout=out)
        output = out.getvalue()
        
        self.assertIn('Skipping existing superuser admin@example.com', output)
        
        self.existing_superuser.refresh_from_db()
        self.assertTrue(self.existing_superuser.is_superuser)
        self.assertTrue(self.existing_superuser.is_staff) 