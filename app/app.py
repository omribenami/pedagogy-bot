import apprise
import yaml
import shutil
import os
import schedule
import time
import re
import json
from os import path
from loguru import logger
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException
from selenium.common.exceptions import InvalidSessionIdException
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import Select
from datetime import date



SCHEDULES = os.getenv("SCHEDULES")

class Crawler:
    def __init__(self):
        self.kids = []
        self.delay = 5
        self.pedagogy_url = "https://pedagogy.co.il/parent.html#!/login"
        self.pedagogy_hw_url = "https://pedagogy.co.il/parent.html#!/learning"
        self.pedagogy_msg_url = "https://pedagogy.co.il/parent.html#!/messages"
        self.pedagogy_evt_url = "https://pedagogy.co.il/parent.html#!/periodic"
        self.user_field = "userid"
        self.password_field = "userpwd"
        self.school_field = "scn"
        self.edu_login_btn = '//*[@id="main-app"]/div/div/div/div/div/div[3]/div/button'
        self.json_dict = {}
        self.notifires = os.getenv("NOTIFIERS")
        self.config_path = 'config/config.yaml'
        self.get_kids()
        self.events = list()
        self.latest_event = '//*[@id="main-app"]/div/div/div/div[3]/div/ul/li[1]'
        self.homeworks = list()
        self.date_today = str(date.today().strftime("%d/%m/%y")).replace("-", "/")

    #### Setting ChromeOptions ####
    def init_browser(self):
        logger.info("Initializing browser")
        self.options = webdriver.ChromeOptions()
        self.options.add_argument("-incognito")
        self.options.add_argument("--headless")
        self.options.add_argument("disable-gpu")
        self.options.add_argument("--no-sandbox")
        self.options.add_argument('--start-maximized')
        self.options.add_argument("--disable-dev-shm-usage")
        self.browser = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=self.options)
        # webdriver.Chrome(executable_path=ChromeDriverManager(version='106.0.5249.61').install(),options=self.options)

    def get_kids(self):
        try:
            logger.info("Loading kids list")
            if not path.exists(self.config_path):
                shutil.copy('config.yaml', self.config_path)
            with open("config/config.yaml", 'r', encoding='utf-8') as stream:
                try:
                    self.kids = yaml.safe_load(stream)
                except yaml.YAMLError as exc:
                    logger.error(exc)
        except Exception as e:
            logger.error(str(e))

    def crowl(self, username, password, school, name):
        logger.info("Crawling")
        try:

            # Open pedagogy login page
            self.browser.get(self.pedagogy_url)
            time.sleep(1)

            WebDriverWait(self.browser, self.delay).until(
                EC.presence_of_element_located((By.ID, self.user_field))).send_keys(username)  # Enter Username
            WebDriverWait(self.browser, self.delay).until(
                EC.presence_of_element_located((By.ID, self.password_field))).send_keys(password)  # enter password
            Select(self.browser.find_element(By.ID, self.school_field)).select_by_value(
                school)  # enter school selection

            # time.sleep(1)
            self.browser.find_element("xpath", self.edu_login_btn).click()  # click login button
            time.sleep(3)  # wait for page to load

            # Scrap tasks status
            if WebDriverWait(self.browser, self.delay).until(EC.url_matches(self.pedagogy_msg_url)):
                logger.info("Logged in successfully")
                time.sleep(3)
            else:
                logger.error(str("Login failed"))

            logger.info("Scrapping homeworks...")
            self.browser.get(self.pedagogy_hw_url)
            time.sleep(3)
            data = self.browser.find_elements(By.CLASS_NAME, 'col-data')
            for i in data:
                if "שיעורי" in i.text or "להביא" in i.text:
                    print("----------")
                    prof = i.find_elements(By.TAG_NAME, 'strong')
                    task = i.find_elements(By.TAG_NAME, 'div')
                    for p in prof:
                        logger.info(p.text.replace(" הוראה בכיתה", ": "))
                        for t in task:
                            sub_task = t.find_elements(By.TAG_NAME, 'div')
                            for s in sub_task:
                                if "שיעורי" in s.text or "להביא" in s.text:
                                    logger.info(s.text)
                                    self.homeworks.append(p.text.replace(" הוראה בכיתה", ": ")+s.text)
            self.json_dict['homeworks'] = self.homeworks

            logger.info("Scrapping events...")
            self.browser.get(self.pedagogy_evt_url)
            time.sleep(3)
            events = self.browser.find_elements(By.XPATH, self.latest_event)
            for i in events:
                if self.date_today in i.text:
                    sub = i.find_elements(By.TAG_NAME, 'strong')
                    logger.info("----------")
                    logger.info(f":דוח הארות והערות")
                    for s in sub:
                        logger.info(s.text)
                        self.events.append(s.text)

            self.json_dict['events'] = self.events
            with open('config/homework.json', 'w', encoding='utf-8') as json_file:
                json.dump(self.json_dict, json_file, indent=4, ensure_ascii=False)

        except Exception as e:
            logger.error(str(e))


def main():
    try:
        for kid in crawler.kids['kids']:
            if not kid['username'] or not kid['password'] or not kid['name'] or not kid['school']:
                logger.warning("Kids list is empty or not configured")
                break
            logger.info("Getting tasks for: " + kid["name"])
            crawler.init_browser()
            crawler.crowl(str(kid['username']), str(kid['password']), str(kid['school']), str(kid['name']))
            logger.debug("Closing browser")
            crawler.browser.quit()
    except Exception as e:
        logger.error(str(e))


if __name__ == "__main__":
    try:
        crawler = Crawler()
        main()
        if not SCHEDULES:
            logger.debug("Setting default schedule to 16:00")
            schedule.every().day.at("16:00").do(main)
        else:
            for _schedule in SCHEDULES.split(','):
                logger.debug("Setting schedule to everyday at " + _schedule)
                schedule.every().day.at(_schedule).do(main)
        while True:
            schedule.run_pending()
            time.sleep(1)
    except Exception as e:
        logger.error(str(e))
