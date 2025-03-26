import time

from selenium import webdriver
from selenium.common import NoSuchElementException
from selenium.webdriver import ActionChains
from selenium.webdriver.common import keys
from selenium.webdriver.common.actions.wheel_input import ScrollOrigin
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC



username = 'glebberkez@gmail.com'
password = 'russian333'
fname = 'Gleb'
lname = 'Berkez'
mobile = '719-494-9508'
email = 'glebberkez@gmail.com'

race = 'White'
gender = 'Male'
veteran = 'No'
disability = 'No'
linkedInProfile = 'www.linkedin.com/in/glebberkez'
website = 'www.frontrangejournal.com'
why_are_you_interested = '?'
relocation = 'Yes'       # Check area first
authorization = 'No'
sponsor = 'No'
compensation = '$70,000 - $80,000'
current_location = 'Colorado Springs'


driver = webdriver.Firefox()
driver.implicitly_wait(5)
driver.get("https://linkedin.com")



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
search_string = 'software engineer'
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
time.sleep(3)
# filter to easy apply
try:
    #filters_button = driver.find_element(By.XPATH, "//div[@class='scaffold-layout-toolbar ']/div/section/div/div/div/div/div/button")
    filters_button = driver.find_element(By.XPATH, "//button[text()='All filters']")
    print("filters_button", filters_button)
    filters_button.click()
    #easy_apply = driver.find_element(By.XPATH, "//div[@class='search-reusables__secondary-filters-filter']/fieldset/div/div")
    #easy_apply = driver.find_element(By.XPATH, "//input[text()='Toggle Easy Apply filter']")
    #easy_apply = driver.find_element(By.XPATH, "//legend[text()='Easy Apply filter']")

    #print("easy_apply", easy_apply.get_attribute("class"))
    #easy_apply_next = driver.find_element(By.XPATH, 'following-sibling::input[1]')
    #easy_apply_parent = easy_apply.find_element(By.XPATH, "..")
    #print("easy_apply_parent", easy_apply_parent)

    #easy_apply_toggle = easy_apply_parent.find_element(By.CSS_SELECTOR, "input")
    easy_apply = driver.find_element(By.XPATH, "//input[@class='input artdeco-toggle__button ']")
    print("easy_apply", easy_apply.get_attribute("type"))


    timeout = 10
    aria_checked = easy_apply.get_attribute('aria-checked')
    print("aria_checked", aria_checked)
    if aria_checked == 'false':

        driver.execute_script("arguments[0].scrollIntoView({ behavior: 'smooth', block: 'center' });", easy_apply)

        try:
            # Wait until the element is clickable
            #element = WebDriverWait(driver, timeout).until(
            #    EC.element_to_be_clickable(easy_apply)
            #)
            #print("element is clickable")
            driver.execute_script("arguments[0].click();", easy_apply)
        #time.sleep(10)
        except:
            print("Element not clickable")
    else:
        print("is it not false")


except:
    print("Vatt are you doing?")



# Go to show results

time.sleep(3)
try:
    show_results = driver.find_element(By.XPATH, "//button[@class='reusable-search-filters-buttons search-reusables__secondary-filters-show-results-button artdeco-button artdeco-button--2 artdeco-button--primary ember-view']")
    #show_results = driver.find_element(By.XPATH, "//span[text()='Show results']")
    #show_results_button = show_results.find_element(By.XPATH, "..")
    show_results.click()
except:
    print("Miss clicked")
time.sleep(3)
########################################
########## EASY APPLY READY ############
########################################






# Get info, save to database
# Get list of jobs
job_list = []
job_company = []
company_list = []

try:

    unordered_list = driver.find_element(By.XPATH, "//div[@class='scaffold-layout__list ']/div/ul")
    jobs = unordered_list.find_elements(By.XPATH, ".//li/div/div/div/div/div/div/a")
    jobs2 = unordered_list.find_element(By.XPATH, ".//li")
    for job in jobs:

        job_title = job.get_attribute("aria-label")
        link = job.get_attribute("href")
        company = job.find_element(By.XPATH, "./../../div[2]/span").text
        location = job.find_element(By.XPATH, "(./../../div)[3]/ul/li/span").text
        job_list.append(job_title)
        job_company.append(company)
        company_list.append(location)

        mydict = { 'job_title': job_title, 'link': link, 'company': company, 'location': location }
        #job_list.append(mydict)


    for i in job_list:
        print(i)
    print("--------------\n")



except NoSuchElementException:
    print("No elements found")

else:
    print("length of jobs: ", len(job_list))

# Scroll down

iframe = driver.find_element(By.XPATH, "//div[@class='scaffold-layout__list ']")
scroll_origin = ScrollOrigin.from_element(iframe)
time.sleep(5)
ActionChains(driver)\
    .scroll_from_origin(scroll_origin, 0, 12000)\
    .perform()




try:

    unordered_list = driver.find_element(By.XPATH, "//div[@class='scaffold-layout__list ']/div/ul")
    jobs = unordered_list.find_elements(By.XPATH, ".//li/div/div/div/div/div/div/a")
    for job in jobs:

        job_title = job.get_attribute("aria-label")
        link = job.get_attribute("href")
        company = job.find_element(By.XPATH, "./../../div[2]/span").text
        location = job.find_element(By.XPATH, "(./../../div)[3]/ul/li/span").text
        job_list.append(job_title)
        job_company.append(company)
        company_list.append(location)

        mydict = { 'job_title': job_title, 'link': link, 'company': company, 'location': location }
        #job_list.append(mydict)


    for i in job_list:
        print(i)

    print("--------------\n")



except NoSuchElementException:
    print("No elements found")

else:
    print("length of jobs: ", len(job_list))



