#!/usr/bin/env python3

import asyncio
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
# import typer
from pathlib import Path
from playwright.async_api import async_playwright, TimeoutError

# TODO: typer

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

# TODO: parse resume for text file (`resume_textfile)

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


async def get_raw_html(url):
    """Get raw HTML from a given URL"""

    with suppress(requests.exceptions.ConnectionError):
        with requests_cache.disabled():
            response = requests.get(url, headers=headers)
            return response.text


async def job_prefs():
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


    async def run(self):
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
        browser = await self.playwright.chromium.launch(**options)
        state = Path("playwright/.auth/state.json")
        if state.is_file():
            context = await browser.new_context(
                viewport={"width":1280,"height":1400},
                storage_state=state._str
            )
        else:
            context = await browser.new_context(
                viewport={"width":1280,"height":1400}
            )
        page = await context.new_page()

        page.set_default_timeout(timeout)

        await page.set_extra_http_headers(headers)

        await page.goto(self.url)

        # save state (cookies, local storage, etc.)
        await context.storage_state(path=state._str)

        # run class methods
        if self.kwargs:
            if self.kwargs['action'] == 'login':
                await self.login(page)
            elif self.kwargs['action'] == 'easy_apply':
                await self.easy_apply(page, self.url)
            elif self.kwargs['action'] == 'greenhouse':
                await self.greenhouse(page, self.url)
            elif self.kwargs['action'] == 'lever':
                await self.lever(page, self.url)

        # ! pause for debugging
        await page.pause()

        # close browser
        await page.close()
        await context.close()
        await browser.close()


    async def login(self, page):
        """Helper method to give user time to log into Glassdoor"""

        print('Waiting for user to log in...')

        while True:
            try:
                await page.wait_for_selector("body.main.loggedIn.lang-en.en-US.gdGrid")
                timestamp = time.strftime("%H:%M:%S", time.localtime())
                print(f"Logged in at {timestamp}")
            except TimeoutError:
                break
            return True


    async def easy_apply(self, page, url):
        """
        Apply to a job listing on Glassdoor directly from the job listing page
        """

        # navigate to the application page
        await page.goto(url)

        async with page.expect_popup() as new_page_info:
            await page.get_by_role("button", name="Easy Apply").click()
        new_page = await new_page_info.value
        await new_page.wait_for_load_state()

        # assign new page url to variable
        ez_url = new_page.url

        # get page html
        html = await new_page.content()

        # # parse html
        # soup = BeautifulSoup(html, 'html.parser')
        # print(soup.prettify())
        # element = soup.find_all("resumeUploadCard-button")

        # elems = await new_page.locator("resumeUploadCard-button").evaluate_all()

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

        # override timeout
        new_page.set_default_timeout(100)

        # iterate through form fields
        for field, value in form_fields.items():
            with suppress(TimeoutError):
                # match statement
                match field:
                    case "input-firstName":
                        await new_page.get_by_test_id(field).fill(value)
                    case "input-lastName":
                        await new_page.get_by_test_id(field).fill(value)
                    case "Phone number":
                        await new_page.get_by_label(field, exact=True).fill(value)
                    case "input-email":
                        await new_page.get_by_test_id(field).fill(value)
                    case "resumeUploadCard":
                        # TODO: QA
                        async with new_page.expect_file_chooser() as file_chooser_info:
                            await new_page.get_by_test_id(field).click()
                        file_chooser = await file_chooser_info.value
                        await file_chooser.set_files(value)
                        await new_page.get_by_role("button", name="Continue").click()
                    case "input-q_.*":
                        await new_page.get_by_test_id(field).fill(value)
                    case "Country":
                        await new_page.get_by_role("combobox", name=field).select_option(value)
                    case "United States Citizen":
                        # await new_page.get_by_text(re.compile(r"United States Citizen|US"))
                        await new_page.locator("label").filter(has_text=r"United States Citizen|US").locator("span").first.click(timeout=5000)
                        # await new_page.get_by_test_id(re.compile(r"input-q_.*")).get_by_text("YES").click()
                    case "I don't wish to answer":
                        await new_page.get_by_text(re.compile(r"I don't wish to answer")).click()
                    case "Don't recommend me for any jobs at other employers.":
                        await new_page.get_by_text(re.compile(r"Don't recommend me for any jobs at other employers.")).click()
                    case "Continue":
                        await new_page.get_by_role("button", name=field).click(timeout=5000)
                    case "Review your application":
                        await new_page.get_by_role("button", name=field).click(timeout=5000)
                        # await page.get_by_role("button", name="Submit application").click()
                    case _:
                        # ! review application
                        await new_page.pause()
                        # pass

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


    async def greenhouse(self, page, url):
        """
        Fill out a Greenhouse application form

        NOTE:
            Greenhouse has a different application form structure than Lever, and thus must be parsed differently
        """

        # navigate to the application page
        await page.goto(url)

        # basic info
        await page.frame_locator("iframe[title=\"Greenhouse Job Board\"]").get_by_label("First Name *").fill(first_name)
        await page.frame_locator("iframe[title=\"Greenhouse Job Board\"]").get_by_label("Last Name *").fill(last_name)
        await page.frame_locator("iframe[title=\"Greenhouse Job Board\"]").get_by_label("Email *").fill(email)
        await page.frame_locator("iframe[title=\"Greenhouse Job Board\"]").get_by_label("Phone *").fill(phone)

        # Upload Resume
        await page.frame_locator("iframe[title=\"Greenhouse Job Board\"]").get_by_role("group", name="Resume/CV").get_by_role("button", name="Attach,").click()
        await page.frame_locator("iframe[title=\"Greenhouse Job Board\"]").get_by_role("group", name="Resume/CV").get_by_role("button", name="Attach,").set_input_files(resume)

        # add linkedin
        await page.frame_locator("iframe[title=\"Greenhouse Job Board\"]").get_by_label("LinkedIn Profile").fill(linkedin)

        # TODO: maybeee
        # * add graduation year
        # * add university
        # * add degree
        # * add major
        # * add website
        # * add work authorization

        # ! pause for debugging
        await page.pause()

        # TODO: enable
        # submit
        # await page.frame_locator("iframe[title=\"Greenhouse Job Board\"]").get_by_role("button", name="Submit Application").click()


    async def lever(self, page, url):
        """Fill out a Lever application form"""

        pass

        # # navigate to the application page
        # driver.find_element_by_class_name('template-btn-submit').click()

        # # basic info

        # # socials

        # # add university

        # # add how you found out about the company

        # # submit resume last so it doesn't auto-fill the rest of the form
        # # since Lever has a clickable file-upload, it's easier to pass it into the webpage
        # driver.find_element_by_name('resume').send_keys(Path("resume.pdf").resolve())
        # driver.find_element_by_class_name('template-btn-submit').click()


async def main(url, *args, **kwargs):
    position_title, location = await job_prefs()

    async with async_playwright() as playwright:
        driver = Driver(playwright, url, *args, **kwargs)
        await driver.run()


if __name__ == "__main__":
    url = "https://www.glassdoor.com/job-listing/devops-engineer-avive-JV_IC1147334_KO0,15_KE16,21.htm?jl=1008587573785&pos=108&ao=1136043&s=58&guid=0000018897b30beba949200790012d9c&src=GD_JOB_AD&t=SR&vt=w&uido=EFD96E67CACCEAC9A7770DF34F9A3B58&ea=1&cs=1_4c522004&cb=1686172273881&jobListingId=1008587573785&jrtk=3-0-1h2br630km6pt801-1h2br63192ci5001-8eefae5135a7da85-&ctt=1686175543650"

    try:
        asyncio.run(main(url, action='easy_apply'))
    except TimeoutError as e:
        print(e)
        pass

    # TODO: uncomment to apply to all jobs
    # for url in urls:
    #     asyncio.run(main(url, action='easy_apply'))
