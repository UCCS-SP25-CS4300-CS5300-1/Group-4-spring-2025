## holy actual fuck please kill me

from __future__ import annotations

import random
import sys
import time
from datetime import datetime, timedelta
import os
import logging
import csv
import re
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium import webdriver
import yaml
import pandas as pd
from bs4 import BeautifulSoup
import openai
from PyPDF2 import PdfReader
import webdriver_manager.chrome as ChromeDriverManager
from selenium.webdriver.chrome.service import Service as ChromeService
from pathlib import Path

ChromeDriverManager = ChromeDriverManager.ChromeDriverManager

logger = logging.getLogger(__name__)


def get_project_root():
    """Get the root directory of the Django project"""
    current_file = Path(__file__).resolve()
    ## applier_pilot -> myproject -> project_root
    return current_file.parent.parent.parent


def setupLogger() -> None:
    dt: str = datetime.strftime(datetime.now(), "%m_%d_%y %H_%M_%S ")

    logs_dir = os.path.join(get_project_root(), 'logs')
    if not os.path.isdir(logs_dir):
        os.mkdir(logs_dir)
    
    log_file = os.path.join(logs_dir, str(dt) + 'applyJobs.logger')
    
    logging.basicConfig(filename=log_file, filemode='w',
                      format='%(asctime)s::%(name)s::%(levelname)s::%(message)s', datefmt='%d-%b-%y %H:%M:%S')
    logger.setLevel(logging.DEBUG)
    c_handler = logging.StreamHandler()
    c_handler.setLevel(logging.DEBUG)
    c_format = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s', '%H:%M:%S')
    c_handler.setFormatter(c_format)
    logger.addHandler(c_handler)


class EasyApplyBot:
    setupLogger()
    MAX_SEARCH_TIME = 60 * 60

    def __init__(self,
                 username,
                 password,
                 phone_number,
                 salary,
                 rate,
                 uploads={},
                 filename='output.csv',
                 blacklist=[],
                 blackListTitles=[],
                 experience_level=None,
                 resume_path=None,
                 openai_api_key=None
                 ) -> None:

        self.project_root = get_project_root()
        dirpath: str = os.getcwd()
        logger.info("current directory is : " + dirpath)
        if(experience_level):
            experience_levels = {
                1: "Entry level",
                2: "Associate",
                3: "Mid-Senior level",
                4: "Director",
                5: "Executive",
                6: "Internship"
            }
            applied_levels = [experience_levels[level] for level in experience_level]
            logger.info("Applying for experience level roles: " + ", ".join(applied_levels))
        else:
            logger.info("Applying for all experience levels")
        

        self.uploads = uploads
        self.salary = salary
        self.rate = rate
        
        if not os.path.isabs(filename):
            filename = os.path.join(self.project_root, filename)
        self.filename = filename
        
        past_ids: list | None = self.get_appliedIDs(filename)
        self.appliedJobIDs: list = past_ids if past_ids != None else []
        
        self.options = self.browser_options()
        self.browser = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=self.options)
        self.wait = WebDriverWait(self.browser, 30)
        self.blacklist = blacklist
        self.blackListTitles = blackListTitles
        self.start_linkedin(username, password)
        self.phone_number = phone_number
        self.experience_level = experience_level

        self.openai_api_key = openai_api_key
        if(not self.openai_api_key):
            logger.warning("No OpenAI API key provided. AI-based question answering will not be available.")
        
        if resume_path:
            if not os.path.isabs(resume_path):
                resume_path = os.path.join(self.project_root, resume_path)
            self.resume_path = resume_path
        else:
            self.resume_path = os.path.join(self.project_root, 'resume.pdf')
            
        self.resume_content = None
        if(os.path.exists(self.resume_path)):
            self.load_resume_content()
        else:
            logger.warning(f"Resume file not found at path: {self.resume_path}. AI-based question answering will not be available.")
        
        self.locator = {
            "next": (By.CSS_SELECTOR, "button[aria-label='Continue to next step']"),
            "review": (By.CSS_SELECTOR, "button[aria-label='Review your application']"),
            "submit": (By.CSS_SELECTOR, "button[aria-label='Submit application']"),
            "error": (By.CLASS_NAME, "artdeco-inline-feedback__message"),
            "upload_resume": (By.XPATH, "//*[contains(@id, 'jobs-document-upload-file-input-upload-resume')]"),
            "upload_cv": (By.XPATH, "//*[contains(@id, 'jobs-document-upload-file-input-upload-cover-letter')]"),
            "follow": (By.CSS_SELECTOR, "label[for='follow-company-checkbox']"),
            "upload": (By.NAME, "file"),
            "search": (By.CLASS_NAME, "jobs-search-results-list"),
            "links": ("xpath", '//div[@data-job-id]'),
            "fields": (By.CLASS_NAME, "jobs-easy-apply-form-section__grouping"),
            "radio_select": (By.CSS_SELECTOR, "input[type='radio']"),
            "multi_select": (By.XPATH, "//*[contains(@id, 'text-entity-list-form-component')]"),
            "text_select": (By.CLASS_NAME, "artdeco-text-input--input"),
            "2fa_oneClick": (By.ID, 'reset-password-submit-button'),
            "easy_apply_button": (By.XPATH, '//button[contains(@class, "jobs-apply-button")]')
        }

        self.qa_file = os.path.join(self.project_root, "qa.csv")
        logger.info(f"QA file path set to: {self.qa_file}")
        self.answers = {}

        ## Load existing QA file if it exists
        if(os.path.exists(self.qa_file)):
            try:
                df = pd.read_csv(self.qa_file)
                for index, row in df.iterrows():
                    self.answers[row['Question']] = row['Answer']
                logger.info(f"Loaded {len(self.answers)} question-answer pairs from {self.qa_file}")
            except Exception as e:
                logger.error(f"Error loading QA file: {e}")
                ## Create a backup of the potentially corrupted file
                if(os.path.exists(self.qa_file)):
                    backup_file = f"qa_backup_{int(time.time())}.csv"
                    try:
                        import shutil
                        shutil.copy2(self.qa_file, backup_file)
                        logger.info(f"Created backup of possibly corrupted QA file at {backup_file}")
                    except Exception as backup_error:
                        logger.error(f"Failed to backup corrupted QA file: {backup_error}")
        else:
            ## Create a new QA file with headers if it doesn't exist
            df = pd.DataFrame(columns=["Question", "Answer"])
            df.to_csv(self.qa_file, index=False, encoding='utf-8')
            logger.info(f"Created new QA file at {self.qa_file}")


    def get_appliedIDs(self, filename) -> list | None:
        try:
            df = pd.read_csv(filename,
                             header=None,
                             names=['timestamp', 'jobID', 'job', 'company', 'attempted', 'result'],
                             lineterminator='\n',
                             encoding='utf-8')

            df['timestamp'] = pd.to_datetime(df['timestamp'], format="%Y-%m-%d %H:%M:%S")
            df = df[df['timestamp'] > (datetime.now() - timedelta(days=2))]
            jobIDs: list = list(df.jobID)
            logger.info(f"{len(jobIDs)} jobIDs found")
            return jobIDs
        except Exception as e:
            logger.info(str(e) + "   jobIDs could not be loaded from CSV {}".format(filename))
            return None

    def browser_options(self):
        options = webdriver.ChromeOptions()
        options.add_argument("--start-maximized")
        options.add_argument("--ignore-certificate-errors")
        options.add_argument('--no-sandbox')
        options.add_argument("--disable-extensions")

        ## hide our asses
        options.add_argument("--disable-blink-features")
        options.add_argument("--disable-blink-features=AutomationControlled")

        return options

    def start_linkedin(self, username, password) -> None:
        logger.info("Logging in.....Please wait :)  ")
        self.browser.get("https://www.linkedin.com/login?trk=guest_homepage-basic_nav-header-signin")
        try:
            user_field = self.browser.find_element(By.ID, "username")
            pw_field = self.browser.find_element(By.ID, "password")
            
            login_button = self.browser.find_element(By.CSS_SELECTOR, "button[type='submit']")
            
            user_field.send_keys(username)
            user_field.send_keys(Keys.TAB)
            time.sleep(2)
            pw_field.send_keys(password)
            time.sleep(2)
            login_button.click()
            time.sleep(15)
            
            if("checkpoint" in self.browser.current_url or "two-step-verification" in self.browser.current_url):
                logger.info("Two-factor authentication detected. Please complete it manually.")
                time.sleep(30)

        except TimeoutException:
            logger.info("TimeoutException! Username/password field or login button not found")
        except Exception as e:
            logger.error(f"Login error: {str(e)}")
            logger.info("LinkedIn may have changed their login page structure. Please check manually.")

    def fill_data(self) -> None:
        self.browser.set_window_size(1, 1)
        self.browser.set_window_position(2000, 2000)

    def start_apply(self, positions, locations) -> None:
        start: float = time.time()
        self.fill_data()
        self.positions = positions
        self.locations = locations
        combos: list = []
        while(len(combos) < len(positions) * len(locations)):
            position = positions[random.randint(0, len(positions) - 1)]
            location = locations[random.randint(0, len(locations) - 1)]
            combo: tuple = (position, location)
            if(combo not in combos):
                combos.append(combo)
                logger.info(f"Applying to {position}: {location}")
                location = "&location=" + location
                self.applications_loop(position, location)
            if(len(combos) > 500):
                break

    def applications_loop(self, position, location):

        jobs_per_page = 0
        start_time: float = time.time()

        self.browser.set_window_position(1, 1)
        self.browser.maximize_window()
        self.browser, _ = self.next_jobs_page(position, location, jobs_per_page, experience_level=self.experience_level)
        logger.info("Looking for jobs.. Please wait..")

        while(time.time() - start_time < self.MAX_SEARCH_TIME):
            try:
                logger.info(f"{(self.MAX_SEARCH_TIME - (time.time() - start_time)) // 60} minutes left in this search")

                ## sleep to make sure everything loads, add random to make us look human.
                randoTime: float = random.uniform(1.5, 2.9)
                logger.debug(f"Sleeping for {round(randoTime, 1)}")
                #time.sleep(randoTime)
                self.load_page(sleep=0.5)

                ## LinkedIn displays the search results in a scrollable <div> on the left side, we have to scroll to its bottom

                ## scroll to bottom

                if(self.is_present(self.locator["search"])):
                    scrollresults = self.get_elements("search")
                    #     self.browser.find_element(By.CLASS_NAME,
                    #     "jobs-search-results-list"
                    # )
                    ## Selenium only detects visible elements; if we scroll to the bottom too fast, only 8-9 results will be loaded into IDs list
                    for i in range(300, 3000, 100):
                        self.browser.execute_script("arguments[0].scrollTo(0, {})".format(i), scrollresults[0])
                    scrollresults = self.get_elements("search")
                    #time.sleep(1)

                ## get job links, (the following are actually the job card objects)
                if(self.is_present(self.locator["links"])):
                    links = self.get_elements("links")

                    jobIDs = {} ##{Job id: processed_status}
                
                    ## children selector is the container of the job cards on the left
                    for link in links:
                            if('Applied' not in link.text): ##checking if applied already
                                if(link.text not in self.blacklist): ##checking if blacklisted
                                    jobID = link.get_attribute("data-job-id")
                                    if(jobID == "search"):
                                        logger.debug("Job ID not found, search keyword found instead? {}".format(link.text))
                                        continue
                                    else:
                                        jobIDs[jobID] = "To be processed"
                    if(len(jobIDs) > 0):
                        self.apply_loop(jobIDs)
                    self.browser, jobs_per_page = self.next_jobs_page(position,
                                                                      location,
                                                                      jobs_per_page, 
                                                                      experience_level=self.experience_level)
                else:
                    self.browser, jobs_per_page = self.next_jobs_page(position,
                                                                      location,
                                                                      jobs_per_page, 
                                                                      experience_level=self.experience_level)


            except Exception as e:
                print(e)
    def apply_loop(self, jobIDs):
        for jobID in jobIDs:
            if(jobIDs[jobID] == "To be processed"):
                applied = self.apply_to_job(jobID)
                if(applied):
                    logger.info(f"Applied to {jobID}")
                else:
                    logger.info(f"Failed to apply to {jobID}")
                jobIDs[jobID] == applied

    def apply_to_job(self, jobID):
        ## get job page
        self.get_job_page(jobID)

        ## let page load
        time.sleep(1)

        ## get easy apply button
        button = self.get_easy_apply_button()


        ## word filter to skip positions not wanted
        if(button is not False):
            if(any(word in self.browser.title for word in self.blackListTitles)):
                logger.info('skipping this application, a blacklisted keyword was found in the job position')
                string_easy = "* Contains blacklisted keyword"
                result = False
            else:
                string_easy = "* has Easy Apply Button"
                logger.info("Clicking the EASY apply button")
                button.click()
                time.sleep(1)
                self.fill_out_fields()
                result: bool = self.send_resume()
                if(result):
                    string_easy = "*Applied: Sent Resume"
                else:
                    string_easy = "*Did not apply: Failed to send Resume"
        elif "You applied on" in self.browser.page_source:
            logger.info("You have already applied to this position.")
            string_easy = "* Already Applied"
            result = False
        else:
            logger.info("The Easy apply button does not exist.")
            string_easy = "* Doesn't have Easy Apply Button"
            result = False


        # position_number: str = str(count_job + jobs_per_page)
        logger.info(f"\nPosition {jobID}:\n {self.browser.title} \n {string_easy} \n")

        self.write_to_file(button, jobID, self.browser.title, result)
        return result

    def write_to_file(self, button, jobID, browserTitle, result) -> None:
        def re_extract(text, pattern):
            target = re.search(pattern, text)
            if(target):
                target = target.group(1)
            return target

        timestamp: str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        attempted: bool = False if(button == False) else True
        job = re_extract(browserTitle.split(' | ')[0], r"\(?\d?\)?\s?(\w.*)")
        company = re_extract(browserTitle.split(' | ')[1], r"(\w.*)")

        toWrite: list = [timestamp, jobID, job, company, attempted, result]
        with open(self.filename, 'a+') as f:
            writer = csv.writer(f)
            writer.writerow(toWrite)

    def get_job_page(self, jobID):

        job: str = 'https://www.linkedin.com/jobs/view/' + str(jobID)
        self.browser.get(job)
        self.job_page = self.load_page(sleep=0.5)
        return self.job_page

    def get_easy_apply_button(self):
        EasyApplyButton = False
        try:
            buttons = self.get_elements("easy_apply_button")
            for button in buttons:
                if("Easy Apply" in button.text):
                    EasyApplyButton = button
                    self.wait.until(EC.element_to_be_clickable(EasyApplyButton))
                else:
                    logger.debug("Easy Apply button not found")
            
        except Exception as e: 
            print("Exception:",e)
            logger.debug("Easy Apply button not found")


        return EasyApplyButton

    def fill_out_fields(self):
        fields = self.browser.find_elements(By.CLASS_NAME, "jobs-easy-apply-form-section__grouping")
        for field in fields:

            if("Mobile phone number" in field.text):
                field_input = field.find_element(By.TAG_NAME, "input")
                field_input.clear()
                field_input.send_keys(self.phone_number)


        return


    def get_elements(self, type) -> list:
        if(type == "fields"):
            ## Try multiple selectors for form fields
            logger.info(f"Looking for form fields using multiple selectors")
            elements = []
            
            ## List of common selectors for form fields
            selectors = [
                (By.CLASS_NAME, "jobs-easy-apply-form-section__grouping"),
                (By.CSS_SELECTOR, "div.jobs-easy-apply-form-section__content"),
                (By.CSS_SELECTOR, "fieldset.artdeco-form-field"),
                (By.CSS_SELECTOR, "div.artdeco-text-input--container"),
                (By.CSS_SELECTOR, ".jobs-easy-apply-form-element"),
                (By.CSS_SELECTOR, "div.fb-dash-form-element")
            ]
            
            ## Try each selector
            for selector in selectors:
                try:
                    found_elements = self.browser.find_elements(selector[0], selector[1])
                    if(found_elements):
                        logger.info(f"Found {len(found_elements)} form fields using selector: {selector}")
                        elements.extend(found_elements)
                except Exception as e:
                    logger.debug(f"Error with selector {selector}: {e}")
            
            ## As a last resort, try to find any input fields directly
            if(not elements):
                try:
                    inputs = self.browser.find_elements(By.CSS_SELECTOR, "input[type='text'], textarea, select")
                    if(inputs):
                        logger.info(f"Found {len(inputs)} input fields directly")
                        elements.extend(inputs)
                except Exception as e:
                    logger.debug(f"Error finding inputs directly: {e}")
            
            return elements
        else:
            ## Original behavior for other element types
            elements = []
            element = self.locator[type]
            if(self.is_present(element)):
                elements = self.browser.find_elements(element[0], element[1])
            return elements

    def is_present(self, locator):
        return len(self.browser.find_elements(locator[0],
                                              locator[1])) > 0

    def send_resume(self) -> bool:
        def is_present(button_locator) -> bool:
            return len(self.browser.find_elements(button_locator[0],
                                                  button_locator[1])) > 0

        try:
            upload_resume_locator = (By.XPATH, '//span[text()="Upload resume"]')
            upload_cv_locator = (By.XPATH, '//span[text()="Upload cover letter"]')
            
            ## Add additional button locators for "Continue" buttons
            continue_buttons = [
                (By.CSS_SELECTOR, "button[aria-label='Continue to next step']"),
                (By.CSS_SELECTOR, "button[aria-label='Continue']"),
                (By.CSS_SELECTOR, "button.artdeco-button--primary"),
                (By.XPATH, "//button[contains(text(), 'Continue')]"),
                (By.XPATH, "//button[contains(text(), 'Next')]")
            ]

            submitted = False
            loop = 0
            max_loops = 5
            previously_answered_questions = set()
            
            while(loop < max_loops):
                loop += 1
                time.sleep(1)
                logger.info(f"Application step {loop}/{max_loops}")
                
                ## Upload resume
                if(is_present(upload_resume_locator)):
                    try:
                        resume_locator = self.browser.find_element(By.XPATH, "//*[contains(@id, 'jobs-document-upload-file-input-upload-resume')]")
                        resume = self.uploads["Resume"]
                        resume_locator.send_keys(resume)
                        logger.info("Uploaded resume")
                    except Exception as e:
                        logger.error(f"Resume upload failed: {e}")
                        
                ## Upload cover letter if possible
                if(is_present(upload_cv_locator)):
                    try:
                        cv = self.uploads["Cover Letter"]
                        cv_locator = self.browser.find_element(By.XPATH, "//*[contains(@id, 'jobs-document-upload-file-input-upload-cover-letter')]")
                        cv_locator.send_keys(cv)
                        logger.info("Uploaded cover letter")
                    except Exception as e:
                        logger.error(f"Cover letter upload failed: {e}")

                ## Check for submit button
                if(len(self.get_elements("submit")) > 0):
                    elements = self.get_elements("submit")
                    for element in elements:
                        try:
                            button = self.wait.until(EC.element_to_be_clickable(element))
                            button.click()
                            logger.info("Application Submitted")
                            submitted = True
                            return submitted
                        except Exception as e:
                            logger.error(f"Failed to click submit button: {e}")

                ## Check for error messages and handle form questions
                elif(len(self.get_elements("error")) > 0):
                    elements = self.get_elements("error")
                    if("application was sent" in self.browser.page_source):
                        logger.info("Application Submitted")
                        submitted = True
                        break
                    elif(len(elements) > 0):
                        ## Process questions once and track answered questions
                        logger.info("Found form with questions that need answers")
                        current_questions = self.get_form_questions()
                        
                        ## Check if we've already answered these exact questions
                        current_questions_set = set(current_questions)
                        if(current_questions_set and current_questions_set.issubset(previously_answered_questions)):
                            logger.info("All questions have already been answered, trying to proceed")
                        else:
                            logger.info("Answering form questions...")
                            answered_questions = self.process_questions()
                            previously_answered_questions.update(answered_questions)
                        
                        ## After answering questions, try to find and click continue/next buttons
                        for locator in continue_buttons:
                            try:
                                continue_btn = self.browser.find_element(locator[0], locator[1])
                                if(continue_btn and continue_btn.is_displayed() and continue_btn.is_enabled()):
                                    logger.info(f"Clicking 'Continue' button: {locator}")
                                    continue_btn.click()
                                    time.sleep(1)
                                    break
                            except Exception as e:
                                logger.debug(f"Continue button not found with locator {locator}: {e}")
                        
                        ## Check if application was submitted
                        if("application was sent" in self.browser.page_source):
                            logger.info("Application Submitted after answering questions")
                            submitted = True
                            break
                            
                        ## If we've tried answering questions multiple times but can't proceed
                        if(loop >= 3):
                            logger.warning("Unable to proceed after answering questions multiple times")
                            logger.info("Skipping this application")
                            submitted = False
                            break
                            
                        continue
                    else:
                        logger.info("Application not submitted")
                        time.sleep(2)
                        break

                ## Try next/review buttons
                else:
                    clicked_button = False
                    
                    ## Try next button
                    if(len(self.get_elements("next")) > 0):
                        elements = self.get_elements("next")
                        for element in elements:
                            try:
                                button = self.wait.until(EC.element_to_be_clickable(element))
                                button.click()
                                logger.info("Clicked 'Next' button")
                                clicked_button = True
                                break
                            except Exception as e:
                                logger.error(f"Failed to click next button: {e}")
                    
                    ## Try review button
                    elif(len(self.get_elements("review")) > 0):
                        elements = self.get_elements("review")
                        for element in elements:
                            try:
                                button = self.wait.until(EC.element_to_be_clickable(element))
                                button.click()
                                logger.info("Clicked 'Review' button")
                                clicked_button = True
                                break
                            except Exception as e:
                                logger.error(f"Failed to click review button: {e}")
                    
                    ## If we couldn't find standard buttons, try the additional continue buttons
                    if(not clicked_button):
                        for locator in continue_buttons:
                            try:
                                continue_btn = self.browser.find_element(locator[0], locator[1])
                                if(continue_btn and continue_btn.is_displayed() and continue_btn.is_enabled()):
                                    logger.info(f"Clicking alternative continue button: {locator}")
                                    continue_btn.click()
                                    clicked_button = True
                                    time.sleep(1)
                                    break
                            except Exception:
                                pass
                    
                    ## If we still couldn't click any button
                    if(not clicked_button and loop > 2):
                        logger.warning("No clickable buttons found after multiple attempts")
                        logger.info("Skipping this application")
                        break

        except Exception as e:
            logger.error(f"Error in send_resume: {e}")
            logger.error("Cannot apply to this job")
            pass

        return submitted

    def get_form_questions(self):
        """Get the text of all questions in the current form"""
        form_elements = self.get_elements("fields")
        questions = []
        
        for field in form_elements:
            try:
                field_text = field.text.strip()
                if(field_text):
                    questions.append(field_text)
            except Exception:
                pass
            
        return questions

    def process_questions(self):
        """Process all questions in the form and return set of answered questions"""
        time.sleep(1)
        logger.info("Looking for questions to answer...")
        form_elements = self.get_elements("fields")
        
        if(not form_elements):
            logger.info("No form elements found to process")
            ## Try to take a screenshot for debugging
            try:
                screenshot_path = f"form_debug_{int(time.time())}.png"
                self.browser.save_screenshot(screenshot_path)
                logger.info(f"Saved screenshot for debugging to {screenshot_path}")
            except Exception as e:
                logger.error(f"Failed to take screenshot: {e}")
            return set()
        
        logger.info(f"Found {len(form_elements)} form elements to process")
        answered_questions = set()
        
        ## Attempt to extract and process questions
        for field in form_elements:
            try:
                ## Get visible text (which may contain the question)
                field_text = field.text.strip()
                logger.info(f"Field text: {field_text}")
                
                ## If field has no text, try to find the label
                if(not field_text):
                    try:
                        ## Look for labels near this field
                        label = field.find_element(By.XPATH, "./preceding::label[1]")
                        field_text = label.text.strip()
                        logger.info(f"Found label text: {field_text}")
                    except:
                        pass
                
                ## Skip if still no question text found
                if(not field_text):
                    logger.info("No question text found in this field, skipping")
                    continue
                
                ## Add to answered questions set
                answered_questions.add(field_text)
                
                ## Process the question and get an answer
                answer = self.ans_question(field_text.lower())
                logger.info(f"Generated answer: {answer}")
                
                ## First try to find radio buttons
                try:
                    radio_buttons = field.find_elements(By.CSS_SELECTOR, "input[type='radio']")
                    if(radio_buttons):
                        logger.info(f"Found {len(radio_buttons)} radio buttons")
                        ## For Yes/No answers, look for matching value
                        for radio in radio_buttons:
                            value = radio.get_attribute("value")
                            if(value and ((answer == "Yes" and value.lower() in ["yes", "true", "1"]) or 
                                         (answer == "No" and value.lower() in ["no", "false", "0"]))):
                                self.browser.execute_script("arguments[0].click();", radio)
                                logger.info(f"Clicked radio button with value: {value}")
                                break
                        continue
                except Exception as e:
                    logger.error(f"Error with radio buttons: {e}")
                
                ## Try to find and fill text inputs
                try:
                    text_inputs = field.find_elements(By.CSS_SELECTOR, "input[type='text'], textarea")
                    if(text_inputs):
                        for input_field in text_inputs:
                            input_field.clear()
                            input_field.send_keys(answer)
                            logger.info(f"Filled text input with: {answer}")
                        continue
                except Exception as e:
                    logger.error(f"Error with text inputs: {e}")
                    
                ## Try to find and select dropdown options
                try:
                    selects = field.find_elements(By.TAG_NAME, "select")
                    if(selects):
                        for select_field in selects:
                            from selenium.webdriver.support.ui import Select
                            select = Select(select_field)
                            options = select.options
                            
                            option_texts = [o.text.strip() for o in options]
                            logger.info(f"Available dropdown options: {option_texts}")
                            
                            found_match = False
                            answer_lower = answer.lower().strip()
                            
                            for option in options:
                                option_text = option.text.strip()
                                if(option_text.lower() == answer_lower):
                                    logger.info(f"Found exact case-insensitive match: '{option_text}'")
                                    select.select_by_visible_text(option_text)
                                    found_match = True
                                    break
                            
                            ## If no exact match, try partial match
                            if(not found_match):
                                for option in options:
                                    option_text = option.text.strip()
                                    if((answer_lower in option_text.lower()) or 
                                        (option_text.lower() in answer_lower)):
                                        logger.info(f"Found partial match: '{option_text}' for '{answer}'")
                                        select.select_by_visible_text(option_text)
                                        found_match = True
                                        break
                            
                            ## If still no match, select first non-empty option
                            if(not found_match and len(options) > 1):
                                for option in options:
                                    option_text = option.text.strip()
                                    if(option_text and not option_text.lower() in ["select an option", "please select"]):
                                        logger.info(f"No match found. Selecting first valid option: '{option_text}'")
                                        select.select_by_visible_text(option_text)
                                        break
                            
                            logger.info(f"Dropdown selection completed")
                        continue
                except Exception as e:
                    logger.error(f"Error with select dropdown: {e}")
                
                logger.warning(f"Could not find appropriate input element for question: {field_text}")
                
            except Exception as e:
                logger.error(f"Error processing field: {e}")
                continue
        
        return answered_questions

    def ans_question(self, question): ##refactor this to an ans.yaml file
        """Answer questions based on resume content if available, otherwise use default answers"""
        ## Check if we have a stored answer for this question
        if(question in self.answers and self.answers[question] != "user provided"):
            logger.info(f"Using stored answer from QA file for: {question}")
            return self.answers[question]
        
        ## If we have resume content and OpenAI API key, use AI to answer
        if(self.resume_content and self.openai_api_key and not "wish not to answer" in question.lower()):
            try:
                logger.info(f"Using AI to answer: {question}")
                ai_answer = self.get_ai_answer(question)
                if(ai_answer):
                    ## Save AI generated answer to qa.csv
                    self.save_answer_to_csv(question, ai_answer)
                    return ai_answer
                else:
                    logger.warning("AI returned empty answer, falling back to pattern matching")
            except Exception as e:
                logger.error(f"Error using AI to answer question: {str(e)}")
                logger.warning("Falling back to pattern matching for answering")
        elif(not self.resume_content):
            logger.warning("No resume content available for AI answering")
        elif(not self.openai_api_key):
            logger.warning("No OpenAI API key available for AI answering")
            
        ## Pattern matching for common questions
        answer = None
        if("how many" in question):
            answer = "1"
        elif("experience" in question):
            answer = "1"
        elif("sponsor" in question):
            answer = "No"
        elif('do you ' in question):
            answer = "Yes"
        elif("have you " in question):
            answer = "Yes"
        elif("US citizen" in question):
            answer = "Yes"
        elif("are you " in question):
            answer = "Yes"
        elif("salary" in question):
            answer = self.salary
        elif("can you" in question):
            answer = "Yes"
        elif("gender" in question):
            answer = "Male"
        elif("race" in question):
            answer = "Wish not to answer"
        elif("lgbtq" in question):
            answer = "Wish not to answer"
        elif("ethnicity" in question):
            answer = "Wish not to answer"
        elif("nationality" in question):
            answer = "Wish not to answer"
        elif("government" in question):
            answer = "I do not wish to self-identify"
        elif("are you legally" in question):
            answer = "Yes"
        else:
            logger.info("Not able to answer question automatically. Please provide answer")
            answer = "user provided"
            time.sleep(15)

        logger.info("Answering question: " + question + " with answer: " + answer)

        ## Save the answer to qa.csv
        self.save_answer_to_csv(question, answer)
        
        return answer

    def save_answer_to_csv(self, question, answer):
        """Save a question-answer pair to the CSV file"""
        try:
            ## Clean up question text - replace newlines with spaces to avoid CSV issues
            ## This preserves the question but makes it safer for CSV storage
            clean_question = question.replace('\n', ' ').replace('\r', ' ')
            while('  ' in clean_question):
                clean_question = clean_question.replace('  ', ' ')
            
            ## Always update the in-memory dictionary with original question
            self.answers[question] = answer
            
            ## Create a DataFrame for the new row with cleaned question
            new_data = pd.DataFrame({"Question": [clean_question], "Answer": [answer]})
            
            ## Check if file exists
            if(os.path.exists(self.qa_file)):
                ## File exists, check if we should update or append
                try:
                    ## Try to read the existing file
                    df = pd.read_csv(self.qa_file)
                    
                    ## Check if question already exists - using fuzzy matching
                    exact_match = clean_question in df['Question'].values
                    
                    if(exact_match):
                        ## Update the existing question with the new answer
                        df.loc[df['Question'] == clean_question, 'Answer'] = answer
                        ## Write the entire updated DataFrame back to the file
                        df.to_csv(self.qa_file, index=False, quoting=csv.QUOTE_ALL, encoding='utf-8')
                        logger.info(f"Updated existing question in QA file with answer: '{answer}'")
                    else:
                        ## Try fuzzy matching to find similar questions
                        found_match = False
                        for idx, row_question in enumerate(df['Question']):
                            ## Simple similarity - remove spaces and compare lowercase
                            q1 = ''.join(clean_question.lower().split())
                            q2 = ''.join(str(row_question).lower().split())
                            
                            ## If 90% similar, consider it the same question
                            if(q1 in q2 or q2 in q1 or (len(q1) > 0 and len(q2) > 0 and 
                                                       (float(len(set(q1) & set(q2))) / float(len(set(q1) | set(q2)))) > 0.9)):
                                df.loc[idx, 'Answer'] = answer
                                found_match = True
                                df.to_csv(self.qa_file, index=False, quoting=csv.QUOTE_ALL, encoding='utf-8')
                                logger.info(f"Updated similar question in QA file with answer: '{answer}'")
                                break
                        
                        if(not found_match):
                            ## Append the new question-answer pair
                            new_data.to_csv(self.qa_file, mode='a', header=False, index=False, 
                                           quoting=csv.QUOTE_ALL, encoding='utf-8')
                            logger.info(f"Appended new question to QA file with answer: '{answer}'")
                except Exception as e:
                    ## If there's an error reading the file, just append with proper quoting
                    logger.error(f"Error reading existing QA file: {e}, will append")
                    new_data.to_csv(self.qa_file, mode='a', header=False, index=False, 
                                   quoting=csv.QUOTE_ALL, encoding='utf-8')
            else:
                ## File doesn't exist, create it with headers and proper quoting
                new_data.to_csv(self.qa_file, index=False, quoting=csv.QUOTE_ALL, encoding='utf-8')
                logger.info(f"Created new QA file with question and answer: '{answer}'")
            
            ## Validate the CSV file after writing
            try:
                test_df = pd.read_csv(self.qa_file)
                logger.info(f"CSV file validated successfully - contains {len(test_df)} questions")
            except Exception as val_err:
                logger.error(f"Warning: CSV file may be corrupted: {val_err}")
            
        except Exception as e:
            logger.error(f"Error saving to QA file: {e}")
            ## Try to create a backup of the data
            try:
                backup_file = f"qa_backup_{int(time.time())}.csv"
                new_data.to_csv(backup_file, index=False, quoting=csv.QUOTE_ALL, encoding='utf-8')
                logger.info(f"Created backup of QA data at {backup_file}")
            except Exception as backup_error:
                logger.error(f"Failed to create backup: {backup_error}")

    def get_ai_answer(self, question):
        """Use OpenAI to generate an appropriate answer based on resume content"""
        if(not self.openai_api_key):
            raise ValueError("OpenAI API key is not set")
        
        if(not self.resume_content):
            raise ValueError("Resume content is not loaded")
        
        openai.api_key = self.openai_api_key
        
        try:
            logger.info("Calling OpenAI API...")
            response = openai.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are an assistant helping with job applications. Your task is to answer job application questions based on the resume provided. Answer with ONLY the specific answer, nothing more. For experience questions with years, if resume shows relevant experience, answer with the years shown, otherwise default to '1'. For yes/no questions, answer 'Yes' if qualified, 'No' if clearly not qualified. For multiple choice questions, respond with only the letter/option that matches best."},
                    {"role": "user", "content": f"Resume:\n{self.resume_content}\n\nJob Application Question: {question}\n\nProvide ONLY the specific answer, no explanation."}
                ],
                max_tokens=50,
                temperature=0.1
            )
            answer = response.choices[0].message.content.strip()
            logger.info(f"AI generated answer: {answer}")
            return answer
        except Exception as e:
            logger.error(f"OpenAI API error: {str(e)}")
            raise RuntimeError(f"OpenAI API error: {str(e)}")

    def load_page(self, sleep=1):
        scroll_page = 0
        while(scroll_page < 4000):
            self.browser.execute_script("window.scrollTo(0," + str(scroll_page) + " );")
            scroll_page += 500
            time.sleep(sleep)

        if(sleep != 1):
            self.browser.execute_script("window.scrollTo(0,0);")
            time.sleep(sleep)

        page = BeautifulSoup(self.browser.page_source, "lxml")
        return page


    def next_jobs_page(self, position, location, jobs_per_page, experience_level=[]):
        ## Construct the experience level part of the URL
        experience_level_str = ",".join(map(str, experience_level)) if experience_level else ""
        experience_level_param = f"&f_E={experience_level_str}" if experience_level_str else ""
        self.browser.get(
            ## URL for jobs page
            "https://www.linkedin.com/jobs/search/?f_LF=f_AL&keywords=" +
            position + location + "&start=" + str(jobs_per_page) + experience_level_param)
        #self.avoid_lock()
        logger.info("Loading next job page?")
        self.load_page()
        return (self.browser, jobs_per_page)

    def load_resume_content(self):
        """Load and extract text from the resume PDF"""
        try:
            logger.info(f"Loading resume from {self.resume_path}")
            reader = PdfReader(self.resume_path)
            text = ""
            for page in reader.pages:
                text += page.extract_text()
            
            ## Validate that we actually got meaningful content
            if(not text or len(text.strip()) < 50):
                logger.error(f"Resume content seems too short or empty ({len(text)} chars)")
                raise ValueError("Resume content seems too short or empty")
            
            self.resume_content = text
            logger.info(f"Successfully loaded resume content ({len(text)} characters) from {self.resume_path}")
            
            ## Log a sample of the content to verify it looks reasonable
            sample = text[:100] + "..." if(len(text) > 100) else text
            logger.info(f"Resume sample: {sample}")
            
        except Exception as e:
            logger.error(f"Failed to load resume: {str(e)}")
            self.resume_content = None
            raise RuntimeError(f"Failed to load resume: {str(e)}")




if(__name__ == '__main__')  :

    with open("config.yaml", 'r') as stream:
        try:
            parameters = yaml.safe_load(stream)
        except yaml.YAMLError as exc:
            raise exc

    assert len(parameters['positions']) > 0
    assert len(parameters['locations']) > 0
    assert parameters['username'] is not None
    assert parameters['password'] is not None
    assert parameters['phone_number'] is not None

    ## Check resume path and OpenAI API key
    resume_path = parameters.get('resume_path')
    openai_api_key = parameters.get('openai_api_key')
    
    if(resume_path and not os.path.exists(resume_path)):
        logger.warning(f"⚠️ Resume file not found at path: {resume_path}")
        use_ai = input("Resume file not found. Do you want to continue without AI question answering? (y/n): ")
        if(use_ai.lower() != 'y'):
            logger.error("Exiting as resume file is required for AI functionality")
            sys.exit(1)
    
    if(not openai_api_key):
        logger.warning("⚠️ No OpenAI API key provided in config.yaml")
        use_ai = input("No OpenAI API key found. Do you want to continue without AI question answering? (y/n): ")
        if(use_ai.lower() != 'y'):
            logger.error("Exiting as OpenAI API key is required for AI functionality")
            sys.exit(1)

    if('uploads' in parameters.keys() and type(parameters['uploads']) == list):
        raise Exception("uploads read from the config file appear to be in list format" +
                        " while should be dict. Try removing '-' from line containing" +
                        " filename & path")

    logger.info({k: parameters[k] for k in parameters.keys() if k not in ['username', 'password', 'openai_api_key']})

    output_filename: list = [f for f in parameters.get('output_filename', ['output.csv']) if f is not None]
    output_filename: list = output_filename[0] if(len(output_filename) > 0) else 'output.csv'
    blacklist = parameters.get('blacklist', [])
    blackListTitles = parameters.get('blackListTitles', [])

    uploads = {} if(parameters.get('uploads', {}) is None) else parameters.get('uploads', {})
    for key in uploads.keys():
        assert uploads[key] is not None

    locations: list = [l for l in parameters['locations'] if l is not None]
    positions: list = [p for p in parameters['positions'] if p is not None]

    bot = EasyApplyBot(parameters['username'],
                       parameters['password'],
                       parameters['phone_number'],
                       parameters['salary'],
                       parameters['rate'], 
                       uploads=uploads,
                       filename=output_filename,
                       blacklist=blacklist,
                       blackListTitles=blackListTitles,
                       experience_level=parameters.get('experience_level', None),
                       resume_path=resume_path,
                       openai_api_key=openai_api_key
                       )
    bot.start_apply(positions, locations)

def applier_pilot(search_term, LI_username, LI_password, amount_of_jobs):
    """
    Function for backward compatibility with the old login.py module.
    
    Args:
        search_term (str): The job search term
        LI_username (str): LinkedIn username
        LI_password (str): LinkedIn password
        amount_of_jobs (int): Maximum number of jobs to return
        
    Returns:
        list: A list of job dictionaries with keys: job_title, company, link, location
    """

    setupLogger()
    
    project_root = get_project_root()
    
    output_file = os.path.join(project_root, 'output.csv')
    
    bot = EasyApplyBot(
        username=LI_username,
        password=LI_password,
        phone_number="0000000000",  
        salary="60,000",            
        rate="25",                
        uploads={},                
        filename=output_file,       
        blacklist=[],              
        blackListTitles=[]          
    )
    
    bot.start_apply([search_term], ['Remote'])
    
    job_list = []
    
    if(os.path.exists(bot.filename)):
        try:
            df = pd.read_csv(bot.filename,
                            header=None,
                            names=['timestamp', 'jobID', 'job', 'company', 'attempted', 'result'],
                            lineterminator='\n',
                            encoding='utf-8')
            
            for _, row in df.iterrows():
                if not pd.isna(row['jobID']):
                    job_info = {
                        'job_title': row['job'] if not pd.isna(row['job']) else f"Job {row['jobID']}",
                        'company': row['company'] if not pd.isna(row['company']) else "Unknown Company",
                        'link': f"https://www.linkedin.com/jobs/view/{row['jobID']}",
                        'location': 'Remote'
                    }
                    job_list.append(job_info)
        except Exception as e:
            logger.error(f"Error reading output file: {e}")
    
    if not job_list and hasattr(bot, 'appliedJobIDs') and bot.appliedJobIDs:
        for jobID in bot.appliedJobIDs:
            job_info = {
                'job_title': f"Job {jobID}",
                'company': "Applied via LinkedIn",
                'link': f"https://www.linkedin.com/jobs/view/{jobID}",
                'location': 'Remote'
            }
            job_list.append(job_info)
    
    return job_list[:amount_of_jobs]
