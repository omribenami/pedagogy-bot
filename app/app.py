import apprise
import yaml
import shutil
import os
import schedule
import time
import re
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


SCHEDULES=os.getenv("SCHEDULES")


class Crawler:
    def __init__(self):
        self.kids = []
        self.delay = 5
        self.pedagogy_url = "https://pedagogy.co.il/parent.html#!/login"
        self.user_field = "userid"
        self.password_field = "userpwd"
        self.school_field = "scn"
        self.edu_login_btn = '//*[@id="main-app"]/div/div/div/div/div/div[3]/div/button'
        self.todo = ""
        self.tofix = ""
        self.wating = ""
        self.checked = ""
        self.apobj = apprise.Apprise()
        self.notifires = os.getenv("NOTIFIERS")
        self.config_path = 'config/config.yaml'
        self.get_kids()



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
        self.browser = webdriver.Chrome(service=Service(ChromeDriverManager().install()),options=self.options)
            # webdriver.Chrome(executable_path=ChromeDriverManager(version='106.0.5249.61').install(),options=self.options)


    def get_kids(self):
        try:
            logger.info("Loading kids list")
            if not path.exists(self.config_path):
                shutil.copy('config.yaml', self.config_path)
            with open("config/config.yaml",'r',encoding='utf-8') as stream:
                try:
                    self.kids = yaml.safe_load(stream)
                except yaml.YAMLError as exc:
                    logger.error(exc)
        except Exception as e:
            logger.error(str(e))


    def crowl(self, username, password, school):
        logger.info("Crowling")
        try:

            # Open pedagogy login page
            self.browser.get(self.pedagogy_url)
            time.sleep(1)

            WebDriverWait(self.browser, self.delay).until(EC.presence_of_element_located((By.ID, self.user_field))).send_keys(username)  # Enter Username
            WebDriverWait(self.browser, self.delay).until(EC.presence_of_element_located((By.ID, self.password_field))).send_keys(password)  # enter password
            Select(self.browser.find_element(By.ID, self.school_field)).select_by_value(school)  # enter school selection

            # time.sleep(1)
            self.browser.find_element("xpath", self.edu_login_btn).click()  # click login button
            time.sleep(3)  # wait for page to load

            # Scrap tasks status
            if WebDriverWait(self.browser, self.delay).until(EC.url_matches("https://pedagogy.co.il/parent.html#!/messages")):
                logger.info("Logged in successfully")
                time.sleep(3)
            else:
                logger.error(str("Login failed"))
            logger.info("Scrapping...")
            self.browser.get("https://pedagogy.co.il/parent.html#!/learning")
            time.sleep(3)
            data = self.browser.find_elements(By.CLASS_NAME, 'col-data')
            with open('config/homework.yaml', 'w', encoding='utf8') as txt:
                for i in data:
                    if  "שיעורי" in i.text or "להביא" in i.text:
                        print("----------")
                        print(i.text)
                        txt.write(i.text + '')
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
            crawler.crowl(str(kid['username']),str(kid['password']),str(kid['school']))
            title = "מצב שיעורי בית של " + kid['name']
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


