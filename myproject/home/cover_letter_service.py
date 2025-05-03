"""
This file contains the code for the cover letter service.
"""

import io
import os
import datetime
from typing import Dict, Optional

import requests
from pypdf import PdfReader
from django.conf import settings
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer
from reportlab.lib.enums import TA_CENTER

class CoverLetterService:
    """Service to handle cover letter generation."""

    API_URL = "https://api.openai.com/v1/chat/completions"

    @staticmethod
    def get_api_key():
        """Get OpenAI API key from environment or settings."""
        api_key = os.environ.get('OPENAI_API_KEY')

        if not api_key and hasattr(settings, 'OPENAI_API_KEY'):
            api_key = settings.OPENAI_API_KEY

        return api_key

    @staticmethod
    def generate_cover_letter(job_description: str, resume_text: Optional[str] = None,
                            user_info: Optional[Dict] = None) -> str:
        """
        Generate a cover letter based on job description and optionally resume text.

        Args:
            job_description: The job description text
            resume_text: Optional text extracted from the user's resume
            user_info: Optional dict with user's name, email, phone, etc.

        Returns:
            The generated cover letter text
        """
        if not user_info:
            user_info = {
                "name": "[Your Name]",
                "email": "[Your Email]",
                "phone": "[Your Phone]",
                "address": "[Your Address]"
            }

        today = datetime.datetime.now().strftime("%B %d, %Y")
        template_letter = CoverLetterService._get_template_cover_letter(user_info, today)

        try:
            api_key = CoverLetterService.get_api_key()

            if not api_key:
                print("OpenAI API key not found. Using template cover letter.")
                return template_letter

            prompt = f"""Please write a professional
            cover letter for a job application based on this information:

JOB DESCRIPTION:
{job_description}

TODAY'S DATE:
{today}

APPLICANT INFO:
Name: {user_info.get('name', '[Your Name]')}
Email: {user_info.get('email', '[Your Email]')}
Phone: {user_info.get('phone', '[Your Phone]')}
Address: {user_info.get('address', '')}

"""

            if resume_text:
                prompt += f"""RESUME INFORMATION:
{resume_text}

Based on my resume and the job description, craft a tailored cover letter highlighting the most relevant skills and experiences.
"""
            else:
                prompt += """I don't have my resume to share, so
                please create a general but 
                persuasive cover letter with placeholders where 
                I should add my specific experiences.
"""

            prompt += """
FORMAT:
- Include today's date, my contact information, and employer info block
- Start with a professional greeting
- 3-4 paragraphs total (intro, 1-2 body paragraphs, conclusion)
- A professional sign-off
- Don't artificially flatter the company
- Focus on how my skills can benefit them
- Keep the total length under 400 words
"""

            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}"
            }

            data = {
                "model": "gpt-4o",
                "messages": [
                {"role": "system",
                "content": "You are an expert at writing compelling, professional cover letters."},
                {"role": "user", "content": prompt}
                ],
                "temperature": 0.7,
                "max_tokens": 1500
            }

            response = requests.post(
                CoverLetterService.API_URL,
                headers=headers,
                json=data,
                timeout=30
            )

            if response.status_code == 200:
                result = response.json()
                return result["choices"][0]["message"]["content"].strip()

            print(f"OpenAI API error: {response.status_code}, {response.text}")
            return template_letter

        except requests.RequestException as e:
            print(f"Error generating cover letter: {e}")
            return template_letter

    @staticmethod
    def _get_template_cover_letter(user_info, date):
        """Returns a template cover letter if the API call fails."""
        name = user_info.get('name', '[Your Name]')
        email = user_info.get('email', '[Your Email]')
        phone = user_info.get('phone', '[Your Phone]')
        address = user_info.get('address', '[Your Address]')

        return f"""{date}

{name}
{address}
{phone}
{email}

[Employer Name]
[Employer Address]

Dear Hiring Manager,

I am writing to express my interest in the [Position Title] role at [Company Name]. With my background in [Your Field/Industry], I believe I would be a valuable addition to your team.

Based on the job description, my qualifications align well with what you're seeking. I have experience in [Key Skill 1], [Key Skill 2], and [Key Skill 3], which would allow me to contribute effectively to your organization.

I am particularly drawn to [Company Name] because of [something specific about the company]. I am confident that my skills in [relevant skill] combined with my passion for [relevant industry/field] make me well-suited for this role.

I would welcome the opportunity to discuss how my background and skills would be a good match for the [Position Title] position. Thank you for considering my application.

Sincerely,

{name}
"""

    @staticmethod
    def create_cover_letter_pdf(cover_letter_text: str) -> bytes:
        """
        Create a PDF file from the cover letter text.

        Args:
            cover_letter_text: The cover letter text
            filename: The base filename (without extension)

        Returns:
            The PDF data as bytes
        """
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter,
                              rightMargin=72, leftMargin=72,
                              topMargin=72, bottomMargin=72)

        styles = getSampleStyleSheet()
        styles.add(ParagraphStyle(name='Justify', alignment=1))
        styles.add(ParagraphStyle(name='Center', alignment=TA_CENTER))

        lines = cover_letter_text.split('\n')
        story = []

        for line in lines:
            if line.strip():
                p = Paragraph(line, styles["Normal"])
                story.append(p)
            else:
                story.append(Spacer(1, 12))

        doc.build(story)

        pdf_data = buffer.getvalue()
        buffer.close()

        return pdf_data

    @staticmethod
    def extract_text_from_resume(resume_file) -> Optional[str]:
        """
        Extract text from a resume PDF file.

        Args:
            resume_file: The resume file object

        Returns:
            The extracted text or None if extraction fails
        """
        try:
            reader = PdfReader(resume_file)
            text = ""
            for page in reader.pages:
                text += page.extract_text()
            return text
        except (FileNotFoundError, ValueError) as e:
            print(f"Error extracting text from resume: {e}")
            return None
