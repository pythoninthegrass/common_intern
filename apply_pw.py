#!/usr/bin/env python3

import json
import re
import requests
import requests_cache
import time
import typer
from bs4 import BeautifulSoup
from contextlib import suppress
from decouple import config, UndefinedValueError
from icecream import ic
from pathlib import Path
from playwright.sync_api import sync_playwright, TimeoutError

# env vars
url = config(
    'URL',
    default='https://www.glassdoor.com/profile/login_input.htm'
)
headless_toggle = config('HEADLESS', default=False, cast=bool)  # default is False
username = config('USERNAME', default='spiritualized@gmail.com')
password = config('PASSWORD', default='correcthorsebatterystaple')
first_name = config('FIRST_NAME', default='Yosemite')
last_name = config('LAST_NAME', default='Sam')
location = config('LOCATION')
first_name = config('FIRST_NAME')
last_name = config('LAST_NAME')
email = config('EMAIL')
phone = config('PHONE')
zip_code = config('ZIP_CODE')
country = config('COUNTRY')
org = config('ORG')
resume = config('RESUME')
resume_textfile = config('RESUME_TEXTFILE')
linkedin = config('LINKEDIN')
website = config('WEBSITE')
github = config('GITHUB')
twitter = config('TWITTER')
grad_month = config('GRAD_MONTH')
grad_year = config('GRAD_YEAR')
university = config('UNIVERSITY')

# dictionary of form fields
form_fields = {
    "input-firstName": first_name,
    "input-lastName": last_name,
    "Phone number": phone,
    "input-email": email,
    "resumeUploadCard": str(Path(resume).resolve()),
    "input-q_.*": zip_code,
    "Country": country,
    "United States Citizen": "",
    "I don't wish to answer": "",
    "Don't recommend me for any jobs at other employers.": "",
    "Continue": "",
    "Review your application": "",
}

# get latest json export
latest_export = max(Path('exports').glob('urls_*.json'))

# read in job listings from exports/urls_*.json
with open(latest_export) as f:
    urls = json.load(f)

# set timeout (e.g., *.click(timeout=10000)))
sec = 10
timeout = sec * 1000

headers = {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Methods': 'GET',
    'Access-Control-Allow-Headers': 'Content-Type',
    'Access-Control-Max-Age': '3600',
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:109.0) Gecko/20100101 Firefox/113.0'
}


def get_raw_html(url):
    """Get raw HTML from a given URL"""

    with suppress(requests.exceptions.ConnectionError):
        with requests_cache.disabled():
            response = requests.get(url, headers=headers)
            return response.text


def job_prefs():
    """Prompt for job preferences if not set in .env file"""

    global position_title, location

    try:
        position_title = config('POSITION_TITLE')
        location = config('LOCATION')
    except UndefinedValueError:
        position_title = typer.prompt("Enter position title")
        location = typer.prompt("Enter location")

    return position_title, location


class Driver:
    """Driver class to handle all browser interactions"""

    def __init__(self, playwright, url, *args, **kwargs):
        self.playwright = playwright
        self.url = url
        self.args = args
        self.kwargs = kwargs


    def run(self):
        headers = {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'GET',
            'Access-Control-Allow-Headers': 'Content-Type',
            'Access-Control-Max-Age': '3600',
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36'
        }

        options = {
            "args": [
                '--disable-blink-features=AutomationControlled',
                '--disable-gpu',
                '--disable-dev-shm-usage',
                '--disable-setuid-sandbox',
                '--no-first-run',
                '--no-sandbox',
                '--no-zygote',
                '--ignore-certificate-errors',
                '--disable-extensions',
                '--disable-infobars',
                '--disable-notifications',
                '--disable-popup-blocking',
                '--remote-debugging-port=9222'
            ],
            "headless": headless_toggle,
            "slow_mo": 100,
            "devtools": False,
        }
        browser = self.playwright.chromium.launch(**options)
        state = Path("playwright/.auth/state.json")
        if state.is_file():
            context = browser.new_context(
                viewport={"width":1280,"height":1400},
                storage_state=state._str
            )
        else:
            context = browser.new_context(
                viewport={"width":1280,"height":1400}
            )
        page = context.new_page()

        page.set_default_timeout(timeout)

        page.set_extra_http_headers(headers)

        page.goto(self.url)

        # save state (cookies, local storage, etc.)
        context.storage_state(path=state._str)

        # run class methods
        if self.kwargs:
            if self.kwargs['action'] == 'login':
                self.login(page)
            elif self.kwargs['action'] == 'scrape_page':
                self.scrape_page(page, self.url)
            elif self.kwargs['action'] == 'easy_apply':
                self.easy_apply(page, self.url)
            elif self.kwargs['action'] == 'greenhouse':
                self.greenhouse(page, self.url)
            elif self.kwargs['action'] == 'lever':
                self.lever(page, self.url)

        # ! pause for debugging
        page.pause()

        # close browser
        # page.close()
        # context.close()
        # browser.close()


    def login(self, page):
        """Helper method to give user time to log into Glassdoor"""

        print('Waiting for user to log in...')

        while True:
            try:
                page.wait_for_selector("body.main.loggedIn.lang-en.en-US.gdGrid")
                timestamp = time.strftime("%H:%M:%S", time.localtime())
                print(f"Logged in at {timestamp}")
            except TimeoutError:
                break
            return True

    # # OG
    # await new_page.get_by_test_id("input-firstName").fill(first_name)
    # await new_page.get_by_test_id("input-lastName").fill(last_name)
    # await new_page.get_by_label("Phone number", exact=True).fill(phone)
    # await new_page.get_by_test_id("input-email").fill(email)
    # await new_page.get_by_role("button", name="Continue").click(timeout=100)
    # await new_page.get_by_test_id("resumeUploadCard").click(timeout=5000)
    # await new_page.get_by_test_id("resumeUploadCard-button").set_input_files(resume)
    # await new_page.get_by_test_id(re.compile(r"input-q_.*")).fill(zip_code)
    # await new_page.get_by_role("combobox", name="Country").select_option(country)
    # await new_page.locator("label").filter(has_text="United States Citizen").locator("span").first.click(timeout=5000)
    # await new_page.locator("label").filter(has_text="I don't wish to answer").locator("span").first.click(timeout=5000)
    # await new_page.locator("label").filter(has_text="Don't recommend me for any jobs at other employers.").locator("span").first.click(timeout=5000)
    # await new_page.get_by_role("button", name="Continue").click(timeout=5000)
    # await new_page.get_by_role("button", name="Review your application").click(timeout=5000)
    # await page.get_by_role("button", name="Submit application").click()

    def scrape_page(self, page, url):
        """Scrape a job listing page for application form fields"""

        # if playwright is not logged in, log in
        if not Path("playwright/.auth/state.json").is_file():
            self.login(page)

        # navigate to the application page
        page.goto(url)

        with page.expect_popup() as new_page_info:
            page.get_by_role("button", name="Easy Apply").click()
        new_page = new_page_info.value
        new_page.wait_for_load_state()
        new_page.set_default_timeout(100)

        # assign new page url to variable
        # ez_url = new_page.url

        # get page html
        return new_page.content()


    def _input_first_name(self, page, field, value):
        page.get_by_test_id(field).fill(value)


    def _input_last_name(self, page, field, value):
        page.get_by_test_id(field).fill(value)


    def _input_phone_number(self, page, field, value):
        page.get_by_label(field, exact=True).fill(value)


    def _input_email(self, page, field, value):
        page.get_by_test_id(field).fill(value)


    def _upload_resume(self, page, field, value):
        with page.expect_file_chooser() as file_chooser_info:
            page.get_by_test_id(field).click()
        file_chooser = file_chooser_info.value
        file_chooser.set_files(value)
        page.get_by_role("button", name="Continue").click()


    def _input_zip_code(self, page, field, value):
        page.get_by_test_id(field).fill(value)


    def _select_country(self, page, field, value):
        page.get_by_role("combobox", name=field).select_option(value)


    def _select_us_citizen(self, page, field, value):
        page.locator("label").filter(has_text=r"United States Citizen|US").locator("span").first.click(timeout=5000)


    def _select_no_answer(self, page, field, value):
        page.get_by_text(re.compile(r"I don't wish to answer")).click()


    def _select_no_recommend(self, page, field, value):
        page.get_by_text(re.compile(r"Don't recommend me for any jobs at other employers.")).click()


    def _click_continue(self, page, field, value):
        page.get_by_role("button", name=field).click(timeout=5000)


    def _click_review(self, page, field, value):
        page.get_by_role("button", name=field).click(timeout=5000)


    def _submit_application(self, page, field, value):
        page.get_by_role("button", name=field).click()


    def easy_apply(self, page, url):
        """Apply to a job listing on Glassdoor directly from the job listing page"""

        # scrape page for available fields
        html = self.scrape_page(page, url)
        soup = BeautifulSoup(html, 'html.parser')
        # ic(soup.prettify())

        # save html for debugging
        if not Path("playwright/soup.html").is_file():
            with open('playwright/soup.html', 'w') as f:
                f.write(soup.prettify())

        try:
            # TODO: check for url first
            # * https://m5.apply.indeed.com/beta/indeedapply/form/contact-info
            # * https://m5.apply.indeed.com/beta/indeedapply/form/resume
            # * https://m5.apply.indeed.com/beta/indeedapply/form/questions/1

            input_first_name = soup.find("input", {"id": "input-firstName"})
            input_last_name = soup.find("input", {"id": "input-lastName"})
            input_phone_number = soup.find("input", {"id": "input-phone"})
            input_email = soup.find("input", {"id": "input-email"})
            resume_upload_card = soup.find("div", {"data-testid": "resumeUploadCard"})

            # TODO: QA (probably need a while loop)
            # contact info
            if input_first_name:
                self._input_first_name(page, "input-firstName", first_name)

            if input_last_name:
                self._input_last_name(page, "input-lastName", last_name)

            if input_phone_number:
                self._input_phone_number(page, "input-phone", phone)

            if input_email:
                self._input_email(page, "input-email", email)

            # resume
            if resume_upload_card:
                self._upload_resume(page, "resumeUploadCard", resume)

            # ! pause for debugging
            page.pause()

            # questions
            self._input_zip_code(page, "input-q_.*", zip_code)
            self._select_country(page, "Country", country)
            self._select_us_citizen(page, "United States Citizen", "")
            self._select_no_answer(page, "I don't wish to answer", "")
            self._select_no_recommend(page, "Don't recommend me for any jobs at other employers.", "")

            # continue
            self._click_continue(page, "Continue", "")
        except TimeoutError:
            pass

        # review
        self._click_review(page, "Review your application", "")


    def greenhouse(self, page, url):
        """
        Fill out a Greenhouse application form

        NOTE:
            Greenhouse has a different application form structure than Lever, and thus must be parsed differently
        """

        # navigate to the application page
        page.goto(url)

        # basic info
        page.frame_locator("iframe[title=\"Greenhouse Job Board\"]").get_by_label("First Name *").fill(first_name)
        page.frame_locator("iframe[title=\"Greenhouse Job Board\"]").get_by_label("Last Name *").fill(last_name)
        page.frame_locator("iframe[title=\"Greenhouse Job Board\"]").get_by_label("Email *").fill(email)
        page.frame_locator("iframe[title=\"Greenhouse Job Board\"]").get_by_label("Phone *").fill(phone)

        # Upload Resume
        page.frame_locator("iframe[title=\"Greenhouse Job Board\"]").get_by_role("group", name="Resume/CV").get_by_role("button", name="Attach,").click()
        page.frame_locator("iframe[title=\"Greenhouse Job Board\"]").get_by_role("group", name="Resume/CV").get_by_role("button", name="Attach,").set_input_files(resume)

        # add linkedin
        page.frame_locator("iframe[title=\"Greenhouse Job Board\"]").get_by_label("LinkedIn Profile").fill(linkedin)

        # ! pause for debugging
        page.pause()

        # TODO: enable
        # submit
        # page.frame_locator("iframe[title=\"Greenhouse Job Board\"]").get_by_role("button", name="Submit Application").click()


    def lever(self, page, url):
        """Fill out a Lever application form"""

        pass


def main(url, *args, **kwargs):
    position_title, location = job_prefs()

    with sync_playwright() as playwright:
        driver = Driver(playwright, url, *args, **kwargs)
        driver.run()


if __name__ == "__main__":
    url = "https://www.glassdoor.com/job-listing/devops-engineer-avive-JV_IC1147334_KO0,15_KE16,21.htm?jl=1008587573785&pos=108&ao=1136043&s=58&guid=0000018897b30beba949200790012d9c&src=GD_JOB_AD&t=SR&vt=w&uido=EFD96E67CACCEAC9A7770DF34F9A3B58&ea=1&cs=1_4c522004&cb=1686172273881&jobListingId=1008587573785&jrtk=3-0-1h2br630km6pt801-1h2br63192ci5001-8eefae5135a7da85-&ctt=1686175543650"

    try:
        main(url, action='easy_apply')
    except TimeoutError as e:
        print(e)
        pass
