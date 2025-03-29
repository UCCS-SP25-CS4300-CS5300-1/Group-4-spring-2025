

def applier_pilot(amount_of_jobs, LI_username, LI_password):


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



    # username = 'glebberkez@gmail.com'
    # password = 'russian333'
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

    # Create functions
    # scroll function scrolls to the bottom of the page for the browser to view hidden HTML values
    def scroll():
        # Scroll all the way down
        iframe = driver.find_element(By.XPATH, "//div[@class='scaffold-layout__list ']")
        scroll_origin = ScrollOrigin.from_element(iframe)
        time.sleep(1)
        ActionChains(driver) \
            .scroll_from_origin(scroll_origin, 0, 12000) \
            .perform()
        time.sleep(1)
        ActionChains(driver) \
            .scroll_from_origin(scroll_origin, 0, 12000) \
            .perform()
        time.sleep(1)
        ActionChains(driver) \
            .scroll_from_origin(scroll_origin, 0, 12000) \
            .perform()
        time.sleep(1)
        ActionChains(driver) \
            .scroll_from_origin(scroll_origin, 0, 12000) \
            .perform()
        time.sleep(1)
        ActionChains(driver) \
            .scroll_from_origin(scroll_origin, 0, 12000) \
            .perform()
        time.sleep(1)
        ActionChains(driver) \
            .scroll_from_origin(scroll_origin, 0, 12000) \
            .perform()

    # Try to login
    try:
        login = driver.find_element(By.LINK_TEXT, "Sign in").click()
    except:
        print("Could not login")

    # Login
    try:
        username_input = driver.find_element(By.CSS_SELECTOR, "input[id='username']").send_keys(LI_username)
        password_input = driver.find_element(By.CSS_SELECTOR, "input[id='password']").send_keys(LI_password)
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
    search_string = 'system admin'
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

    num_jobs_found = int(astring)

    # Get info, save to database
    # Get list of jobs
    job_list = []
    job_company = []
    company_list = []


    mydict = {}
    current_page = 1
    next_page = current_page + 1

    num_pages = 0
    ellipsis = "…"


    # Begin finding jobs. Ends when amount_of_jobs is reached in job_list
    run_program = True
    while run_program:


        scroll()



        # Start collecting jobs
        try:

            unordered_list = driver.find_element(By.XPATH, "//div[@class='scaffold-layout__list ']/div/ul")
            jobs = unordered_list.find_elements(By.XPATH, ".//div/div/div/div/div/div/a")

            for job in jobs:
                job_title = job.get_attribute("aria-label")
                link = job.get_attribute("href")
                company = job.find_element(By.XPATH, "./../../div[2]/span").text
                location = job.find_element(By.XPATH, "(./../../div)[3]/ul/li/span").text

                # job_list.append(job_title)

                mydict = { 'job_title': job_title, 'link': link, 'company': company, 'location': location }
                job_list.append(mydict)
                print("---", job_title, link, company, location)

            print("--------------\n")



        except NoSuchElementException:
            print("No elements found")

        else:
            print("length of jobs: ", len(job_list))


        ### Page Change ###

        unordered_list_pages = driver.find_element(By.XPATH, "//ul[@class='artdeco-pagination__pages artdeco-pagination__pages--number']")
        pages = unordered_list_pages.find_elements(By.XPATH, ".//li")
        print("Pages", pages)


        # Get next page

        # This conditional determines if we need to change pages due to the number of jobs
        # If there are more than 25 job findings, then yes.
        if num_jobs_found > 25:
            page_clicked = False
        else:
            page_clicked = False

        # If the number of jobs found are at least how many we're looking for,
        # return the job_list
        if len(job_list) >= amount_of_jobs:
            return job_list

        while not page_clicked:
            page_tracker = 1


            for page in pages:
                page_number = page.find_element(By.XPATH, ".//button/span").text


                if page_number == ellipsis and page_tracker == 2:
                    print("here 2")
                    page_tracker += 1
                    continue

                if page_number == ellipsis and page_tracker != 2:
                    print("here 1)")
                    page.find_element(By.XPATH, ".//button").click()
                    time.sleep(2)

                    current_page += 1
                    next_page += 1
                    page_tracker += 1       # Not needed


                    page_clicked = True
                    break

                if page_tracker == len(pages):
                    print("Program end")
                    driver.quit()
                    page_clicked = True
                    run_program = False
                    break


                if int(page_number) == next_page:
                    print("here 3")
                    page.find_element(By.XPATH, ".//button").click()
                    time.sleep(2)

                    # Change variables
                    current_page += 1
                    next_page += 1
                    page_tracker += 1

                    # Exit out of page_clicked while loop
                    page_clicked = True
                    break

                else:
                    page_tracker += 1

    # This returns the job list if we gathered all jobs in search results,
    # even if less than amount of jobs parameter
    return job_list