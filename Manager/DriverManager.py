import sys
sys.path.append("./Utility")
from Utility import Util

from webdriver_manager.chrome import ChromeDriverManager
import undetected_chromedriver as uc 
from selenium.webdriver.common.by import By
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException
from selenium_stealth import stealth
from datetime import datetime
import requests
import os
import psutil
from PIL import Image
from bs4 import BeautifulSoup

class WebDriverManager:
    def __init__(self, logger, is_headless=False, is_use_udc=False):
        self.logger = logger
        self.is_headless = is_headless
        self.is_use_udc = is_use_udc
        self.logger.log(log_level="Debug", log_msg="Driver init")
        self.driver = None
        self.open_driver()
        self.process_list = []
        for proc in psutil.process_iter():
            # 프로세스 이름을 ps_name에 할당
            ps_name = proc.name()
            if ps_name == "chrome.exe":
                self.process_list.append(proc.pid)


    def open_driver(self):
        if self.is_use_udc:
            options = uc.ChromeOptions() 
            options.headless = False  # Set headless to False to run in non-headless mode
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument("--disable-notifications")
            if self.is_headless:
                options.add_argument("headless")
            driver = uc.Chrome(use_subprocess=True, options=options)
        
            self.driver = driver
            self.driver.set_page_load_timeout(10)
        else:
            # Chrome driver Manager를 통해 크롬 드라이버 자동 설치 > 최신 버전을 설치 > Service에 저장
            service = Service(excutable_path=ChromeDriverManager().install())
            chrome_options = Options()
            user_agent = "Mozilla/5.0 (Linux; Android 9; SM-G975F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3578.83 Mobile Safari/537.36"
            chrome_options.add_argument('user-agent=' + user_agent)
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument("--disable-notifications")
            chrome_options.add_argument("--disable-blink-features=AnimationControlled")
            chrome_options.add_argument('--start-maximized')
            chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])
            chrome_options.add_argument('--log-level=3') # 브라우저 로그 레벨을 낮춤
            chrome_options.add_argument('--disable-loging') # 로그를 남기지 않음
            if self.is_headless:
                chrome_options.add_argument("headless")
            driver = webdriver.Chrome(options=chrome_options, service=service)
            self.driver = driver
    
    def close_driver(self):
        if self.driver != None:
            pid = self.driver.service.process.pid
            self.driver.close()
            self.driver.quit()
            self.logger.log(log_level="Debug", log_msg=f"Driver PID : {pid}")
            new_process_list = []
            for proc in psutil.process_iter():
                # 프로세스 이름을 ps_name에 할당
                ps_name = proc.name()
                if ps_name == "chrome.exe":
                    new_process_list.append(proc.pid)
            new_process_list = list(set(new_process_list) - set(self.process_list))
            self.logger.log(log_level="Debug", log_msg=f"New pid : {new_process_list}")
            for p in new_process_list:
                os.system("taskkill /pid {} /t".format(pid))
                self.logger.log(log_level="Debug", log_msg=f"Kill pid {pid}")
            self.driver = None
            self.logger.log(log_level="Debug", log_msg=f"Driver deleted")

    def get_page(self, url, max_wait_time = 10):
        is_page_loaded = False
        while(is_page_loaded == False):
            try:
                self.driver.get(url)
                self.driver.implicitly_wait(max_wait_time)
                self.logger.log(log_level="Debug", log_msg=f"Get *{url}* page")
                self.driver.get_screenshot_as_file("temp.png")
                is_page_loaded = True
            except Exception as e:
                self.logger.log(log_level="Debug", log_msg=f"Page load failed : {e}")
                is_page_loaded = False
            #self.driver.minimize_window()

    def get_driver(self):
        return self.driver

    def is_element_exist(self, find_type, element):
        is_exist = False
        try:
            self.driver.find_element(find_type, element)
            is_exist = True
        except NoSuchElementException:
            is_exist = False
        return is_exist

    def download_image(self, img_url, img_name, img_path, download_cnt):
        min_size = 50
        
        #만약 다운로드 시도횟수가 5번을 넘는다면 다운로드 불가능한 이미지로 간주
        if download_cnt > 5:
            self.logger.log(log_level="Error", log_msg=f"Img size is under {min_size}KB or cannot download image \'{img_name}\'")
            return
        try:
            r = requests.get(img_url,headers={'User-Agent': 'Mozilla/5.0'},verify=False,timeout=20)
            with open(f"{img_path}/{img_name}.jpg", "wb") as outfile:
                outfile.write(r.content)
        except Exception as e:
            self.logger.log(log_level="Error", log_msg=f"Image \'{img_name}\' download failed with error : {e}")
            return
        #KB 단위의 이미지 사이즈
        img_size = os.path.getsize(f"{img_path}/{img_name}.jpg") / 1024

        #만약 이미지 크기가 일정 크기 이하라면 다운로드가 실패한것으로 간주, 다시 다운로드
        if img_size < min_size:
            self.logger.log(log_level="Debug", log_msg=f"Image \'{img_name}\' download failed")
            self.download_image(img_url, img_name, img_path, download_cnt + 1)
        else:
            self.logger.log(log_level="Debug", log_msg=f"Image \'{img_name}\' download completed")
        return

    def get_bs_soup(self, url):
        response = requests.get(url)

        if response.status_code == 200:
            html = response.text
            soup = BeautifulSoup(html, 'html.parser')
            return soup
        else : 
            self.logger.log(log_level="Error", log_msg=f"Failed to load page with BeautifulSoup")
            return False
    def __del__(self):
        self.close_driver()