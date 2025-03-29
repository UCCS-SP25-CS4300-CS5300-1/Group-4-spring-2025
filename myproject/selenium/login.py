import time
import math

from selenium import webdriver
from selenium.common import NoSuchElementException
from selenium.webdriver import ActionChains
from selenium.webdriver.common import keys
from selenium.webdriver.common.actions.wheel_input import ScrollOrigin
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.select import Select
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
    enter_credentials = WebDriverWait(driver, 120).until(
        EC.presence_of_all_elements_located((By.XPATH, "//header[@id='global-nav']//li[3]"))
    )

except:
    print("time-out")
    print("try again, except sign in quicker")
    driver.close()


# Click on Jobs tab in profile page
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

# Pause for jobs to load
time.sleep(3)

# Go to filters and switch on easy apply
try:
    filters_button = driver.find_element(By.XPATH, "//button[text()='All filters']")
    filters_button.click()

    easy_apply = driver.find_element(By.XPATH, "//input[@class='input artdeco-toggle__button ']")

    timeout = 10
    aria_checked = easy_apply.get_attribute('aria-checked')

    if aria_checked == 'false':

        driver.execute_script("arguments[0].scrollIntoView({ behavior: 'smooth', block: 'center' });", easy_apply)

        try:
            driver.execute_script("arguments[0].click();", easy_apply)

        except:
            print("Element not clickable")
    else:
        print("is it not false")


except:
    print("Vatt are you doing?")



# Show results of job search query
time.sleep(3)
try:
    show_results = driver.find_element(By.XPATH, "//button[@class='reusable-search-filters-buttons search-reusables__secondary-filters-show-results-button artdeco-button artdeco-button--2 artdeco-button--primary ember-view']")
    show_results.click()
except:
    print("Miss clicked")

time.sleep(3)
########################################
########## EASY APPLY READY ############
########################################



# Find maximum number of pages through total number of jobs found
num_results = driver.find_element(By.XPATH, "//div[@class='scaffold-layout__list ']/header/div/div/small/div/span").text
print("Num results", num_results)
num_results = num_results.split()[0]
time.sleep(5)
num_results = num_results.split(',')

# If results have a comma (ex. 1,200), then pass the comma to make a string that can be converted to int
astring = ''
for i in num_results:
    if i == ',':
        pass
    else:
        astring += i

# 25 results per page, so round up to get max num of pages
max_pages = round(int(astring)/25)
print("max pages", max_pages)


# Get info, save to database
# Get list of jobs
job_list = []
job_company = []
company_list = []


mydict = {}
current_page = 1
next_page = current_page + 1

num_pages = 0


# Scroll down
iteration1 = True
iteration2 = False
while True:

    # Scroll all the way down
    iframe = driver.find_element(By.XPATH, "//div[@class='scaffold-layout__list ']")
    scroll_origin = ScrollOrigin.from_element(iframe)
    time.sleep(1)
    ActionChains(driver)\
        .scroll_from_origin(scroll_origin, 0, 12000)\
        .perform()
    time.sleep(1)
    ActionChains(driver)\
        .scroll_from_origin(scroll_origin, 0, 12000)\
        .perform()
    time.sleep(1)
    ActionChains(driver)\
        .scroll_from_origin(scroll_origin, 0, 12000)\
        .perform()
    time.sleep(1)
    ActionChains(driver)\
        .scroll_from_origin(scroll_origin, 0, 12000)\
        .perform()
    time.sleep(1)
    ActionChains(driver)\
        .scroll_from_origin(scroll_origin, 0, 12000)\
        .perform()
    time.sleep(1)
    ActionChains(driver)\
        .scroll_from_origin(scroll_origin, 0, 12000)\
        .perform()




    # Start collecting jobs
    try:

        unordered_list = driver.find_element(By.XPATH, "//div[@class='scaffold-layout__list ']/div/ul")
        jobs = unordered_list.find_elements(By.XPATH, ".//div/div/div/div/div/div/a")

        for job in jobs:
            job_title = job.get_attribute("aria-label")
            link = job.get_attribute("href")
            company = job.find_element(By.XPATH, "./../../div[2]/span").text
            location = job.find_element(By.XPATH, "(./../../div)[3]/ul/li/span").text

            job_list.append(job_title)

            mydict = { 'job_title': job_title, 'link': link, 'company': company, 'location': location }
            job_list.append(mydict)
            print("---", job_title, link, company, location)

        print("--------------\n")



    except NoSuchElementException:
        print("No elements found")

    else:
        print("length of jobs: ", len(job_list))


    ### Page Change ###
    if max_pages > 1:
        unordered_list_pages = driver.find_element(By.XPATH, "//ul[@class='artdeco-pagination__pages artdeco-pagination__pages--number']")
        pages = unordered_list_pages.find_elements(By.XPATH, ".//li")
        print("Pages", pages)
        # Get next page
        page_clicked = False

        while not page_clicked:
            page_tracker = 1

            for page in pages:
                page_number = page.find_element(By.XPATH, ".//button/span").text

                if iteration1:

                    # For the 9th page of iteration1, we need to click on the ellipsis
                    if next_page == 9:
                        # Clicked to next set of pages. Iteration 1 is over
                        print("next_page", next_page)
                        print("page number", page_number)
                        page.find_element(By.XPATH, "./button").click()
                        time.sleep(2)

                        # Change variables
                        current_page += 1
                        next_page += 1
                        page_clicked = True

                        # Now, only iteration2 will be in effect
                        iteration1 = False
                        iteration2 = True
                        # Exit out of page_clicked while loop
                        break

                    else:
                        if int(page_number) == next_page:
                            page.find_element(By.XPATH, ".//button").click()
                            time.sleep(2)

                            # Change variables
                            current_page += 1
                            next_page += 1

                            # Exit out of page_clicked while loop
                            page_clicked = True
                            break
                elif iteration2:

                    # Skip over the first ellipsis in all subsequent iterations
                    if page_tracker < 3:
                        page_tracker += 1
                        continue

                    # Capture second ellipsis
                    if page_tracker == 9:
                        page.find_element(By.XPATH, "./button").click()
                        time.sleep(2)

                        # Change variables
                        current_page += 1
                        next_page += 1
                        page_clicked = True
                        # Break out of while loop
                        break

                    if int(page_number) == next_page:
                        page.find_element(By.XPATH, "./button").click()
                        time.sleep(2)

                        # Change variables
                        current_page += 1
                        next_page += 1
                        page_clicked = True
                        # Break out of while loop
                        break
                page_tracker += 1
    else:

        print("No need to continue")