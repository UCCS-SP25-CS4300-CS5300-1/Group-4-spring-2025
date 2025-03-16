import time

from selenium import webdriver
from selenium.common import NoSuchElementException
from selenium.webdriver import ActionChains
from selenium.webdriver.common import keys
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

driver = webdriver.Firefox()

driver.implicitly_wait(5)
driver.get("https://linkedin.com")

username = ''
password = ''

# Try to login
try:
    login = driver.find_element(By.LINK_TEXT, "Sign in").click()
except:
    print("Could not login")

# Login
try:
    username_input = driver.find_element(By.CSS_SELECTOR, "input[id='username']").send_keys(username)
    password_input = driver.find_element(By.CSS_SELECTOR, "input[id='password']").send_keys(password)
    driver.find_element(By.XPATH, "//button[@type='submit']").click()


except:
    print("Could not login")
try:
    print("Waiting to be logged in...")
    #ele = driver.find_element(By.XPATH, "//header[@id='global-nav']//li[3]")
    #assert ele == 'Jobs'
    enter_credentials = WebDriverWait(driver, 120).until(
        EC.presence_of_all_elements_located((By.XPATH, "//header[@id='global-nav']//li[3]"))
    )
    print(enter_credentials)
    print("leaving try block")
except:
    print("time-out")
    print("try again, except sign in quicker")
    driver.close()


# Enter jobs
try:
    jobs = driver.find_element(By.XPATH, "//header[@id='global-nav']//li[3]")
    jobs.click()
except:
    print("could not find jobs")
    driver.close()

# Send keys to job search
search_string = 'machine learning intern'
try:
    a = driver.find_element(By.XPATH, "//input[@placeholder='Title, skill or company']")

    actions = ActionChains(driver)
    actions.send_keys_to_element(a, search_string).perform()

    time.sleep(1)
    actions.send_keys(Keys.TAB)
    actions.send_keys(Keys.TAB)
    actions.perform()
    time.sleep(1)
    actions.send_keys('Colorado')
    actions.perform()

    actions.send_keys(Keys.ENTER).perform()
except:
    print("could not send keys")


# Get list of jobs
job_titles = []
try:
    unordered_list = driver.find_element(By.XPATH, "//div[@class='scaffold-layout__list ']/div/ul")
    jobs = unordered_list.find_elements(By.XPATH, ".//li/div/div/div/div/div/div/a")
    for job in jobs:
        job_titles.append(job.get_attribute("aria-label"))
        print(job.get_attribute("aria-label"))

except NoSuchElementException:
    print("No elements found")
else:
    print("length of jobs: ", len(job_titles))

print(job_titles)