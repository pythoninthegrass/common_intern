#!/usr/bin/env python3

import asyncio
import json
import time
# from bs4 import BeautifulSoup
from decouple import config, UndefinedValueError
from pathlib import Path
from playwright.async_api import async_playwright, TimeoutError
import typer

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


# create exports directory
Path("exports").mkdir(parents=True, exist_ok=True)


class Driver:
    """Driver class to handle all browser interactions"""

    def __init__(self, playwright, url, *args, **kwargs):
        self.playwright = playwright
        self.url = url
        self.args = args
        self.kwargs = kwargs


    async def run(self):
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
        await page.goto(self.url)

        # save state (cookies, local storage, etc.)
        await context.storage_state(path=state._str)

        # run class methods
        if self.kwargs:
            if self.kwargs['action'] == 'login':
                await self.login(page)
            elif self.kwargs['action'] == 'go_to_listings':
                await self.go_to_listings(page)
            elif self.kwargs['action'] == 'aggregate_links':
                await self.aggregate_links(page)
            elif self.kwargs['action'] == 'get_urls':
                await self.get_urls(page)
            elif self.kwargs['action'] == 'export_urls':
                await self.export_urls(page)

        # ! pause for debugging
        # await page.pause()

        # close browser
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


    async def go_to_listings(self, page):
        """Navigate to job listing page"""

        print('Navigating to listings...')
        await page.goto('https://www.glassdoor.com/Job/jobs.htm')

        # TODO: debug `waiting for locator("[data-test=\"search-bar-keyword-input\"]")`
        # ! can't run headless as it times out / never appears
        # fill out position and location fields
        await page.locator("[data-test=\"search-bar-keyword-input\"]").click()
        await page.locator("[data-test=\"search-bar-keyword-input\"]").fill(position_title)
        await page.locator("[data-test=\"search-bar-location-input\"]").click()
        await page.locator("[data-test=\"search-bar-location-input\"]").click(click_count=3)
        await page.locator("[data-test=\"search-bar-location-input\"]").fill(location)
        await page.locator("[data-test=\"search-bar-submit\"]").click()

        # show all jobs
        await page.get_by_role("link", name="See All Jobs").click()

        # exit modal
        await page.locator("[data-test=\"modal-jobalert\"]").get_by_role("img").click()


    async def aggregate_links(self, page):
        """Aggregate all URL links"""

        await self.go_to_listings(page)

        all_links = set()

        # get all links on page
        links = await page.query_selector_all("a.jobLink")
        for link in links:
            all_links.add(await link.get_attribute("href"))

        # get next page
        try:
            next_page = await page.query_selector("li.next")
            await next_page.click()
            await page.wait_for_load_state("networkidle")
            all_links.union(self.aggregate_links(page))
        except Exception:
            pass

        return all_links


    async def get_urls(self, page):
        """Create a set of all URLs"""

        all_links = await self.aggregate_links(page)

        all_urls = set()

        for link in all_links:
            url = 'https://www.glassdoor.com' + link
            all_urls.add(url)

        return all_urls


    async def export_urls(self, page):
        """Export urls to a JSON file"""

        all_urls = await self.get_urls(page)

        print(f"Exporting {len(all_urls)} URLs...")

        timestamp = time.strftime("%Y%m%d_%H%M%S", time.localtime())

        fn = f"urls_{timestamp}.json"

        with open(f"exports/{fn}", 'w') as f:
            json.dump(list(all_urls), f, indent=2)

        print(f"Exported {len(all_urls)} URLs to {fn}")


async def main(url, *args, **kwargs):
    position_title, location = await job_prefs()

    async with async_playwright() as playwright:
        driver = Driver(playwright, url, *args, **kwargs)
        await driver.run()


if __name__ == "__main__":
    asyncio.run(main(url, action='export_urls'))
