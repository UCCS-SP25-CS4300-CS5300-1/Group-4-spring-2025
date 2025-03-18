from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from users.models import Profile

class Command(BaseCommand):
    help = 'Creates admin accounts for the team members'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.team_emails = [
            'bdamja2003@gmail.com',
            'glebberkez@gmail.com',
            'ccolbert@uccs.edu',
            'kbilyeu@uccs.edu',
            'azizcsecj@gmail.com',
        ]

    def add_arguments(self, parser):
        parser.add_argument(
            '--emails',
            nargs='+',
            type=str,
            help='List of email addresses to make admins'
        )

    def handle(self, *args, **options):
        emails_to_process = options.get('emails') or self.team_emails

        if(not emails_to_process):
            self.stdout.write(self.style.WARNING('No emails provided and no default emails set'))
            return
        
        ## get existing superusers
        existing_superusers = User.objects.filter(is_superuser=True)
        existing_superusers_emails = [user.email for user in existing_superusers]
        
        for email in existing_superusers_emails:
            self.stdout.write(self.style.SUCCESS(f'Skipping existing superuser {email}'))

        for email in emails_to_process:
            try:
                user = User.objects.get(email=email)
                if(not user.is_superuser):
                    user.is_superuser = True
                    user.is_staff = True
                    user.save()
                    self.stdout.write(self.style.SUCCESS(f'Made existing user {email} a superuser'))
            except User.DoesNotExist:
                base_username = email.split('@')[0]
                username = base_username
                
                counter = 1
                while User.objects.filter(username=username).exists():
                    username = f"{base_username}{counter}"
                    counter += 1
                
                user = User.objects.create_superuser(
                    username=username,
                    email=email,
                    password='ChangeMe123!' 
                )
                if(not hasattr(user, 'profile')):
                    Profile.objects.create(user=user)
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Created new superuser {email} with username "{username}" and temporary password "ChangeMe123!"'
                    )
                ) 