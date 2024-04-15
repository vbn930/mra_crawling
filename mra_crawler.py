from Utility import Util
from Manager import DriverManager
from Utility import LoginModule
from Manager import FileManager

from selenium.webdriver.common.by import By
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException
from dataclasses import dataclass
import pandas as pd
import datetime


@dataclass
class Product:
    code: str
    name: str
    price: str
    dealer_price: str
    description: str
    trans_description: str
    images: list
    option_name: str
    option_value: str
    model: str

@dataclass
class ShopCatrgory:
    make: str
    model: str
    year: str
    href: str

class MRA_Crawler:
    def __init__(self, logger):
        self.file_manager = FileManager.FileManager()
        self.logger = logger
        self.driver_manager = DriverManager.WebDriverManager(self.logger, is_headless=False)
        self.driver = self.driver_manager.driver
        self.file_manager.creat_dir("./temp")
        self.file_manager.creat_dir("./output")
        self.product_numbers = []
        self.product_abbreviations = []
        self.account = []
        self.products = []
        self.data = dict()
        self.data_init()

    def get_init_settings_from_file(self):
        #cvs 파일에서 계정 정보, 브랜드, 브랜드 코드 가져오기
        data = pd.read_csv("./setting.csv").fillna(0)
        account = data["account"].to_list()
        account.append(0)
        account = account[0:account.index(0)]

        start_maker = data["start_maker"].to_list()
        start_maker.append(0)
        start_maker = start_maker[0:start_maker.index(0)]
        
        if len(start_maker) == 0:
            return account[0], account[1], 0, 0, 0
        
        start_model = data["start_model"].to_list()
        start_model.append(0)
        start_model = start_model[0:start_model.index(0)]

        start_year = data["start_year"].to_list()
        start_year.append(0)
        start_year = start_year[0:start_year.index(0)]

        return account[0], account[1], start_maker[0], start_model[0], start_year[0]

    def data_init(self):
        self.data.clear()
        self.data["상품 코드"] = list()
        self.data["상품명"] = list()
        self.data["정상가"] = list()
        self.data["딜러가"] = list()
        self.data["대표 이미지"] = list()
        self.data["상세 이미지"] = list()
        self.data["옵션명"] = list()
        self.data["옵션 내용"] = list()
        self.data["설명"] = list()
        self.data["설명 번역"] = list()
        self.data["모델"] = list()
    
    def add_product_to_data(self, product):
        self.data["상품 코드"].append(product.code)
        self.data["상품명"].append(product.name)
        self.data["정상가"].append(product.price)
        self.data["딜러가"].append(product.dealer_price)
        if len(product.images) == 0:
            self.data["대표 이미지"].append("")
            self.data["상세 이미지"].append("")
        else:
            self.data["대표 이미지"].append(product.images[0])
            img_text = ""
            for img in product.images:
                img_text += img
                if img != product.images[-1]:
                    img_text += "|"
            self.data["상세 이미지"].append(img_text)
        self.data["옵션명"].append(product.option_name)
        self.data["옵션 내용"].append(product.option_value)
        self.data["설명"].append(product.description)
        self.data["설명 번역"].append(product.trans_description)
        self.data["모델"].append(product.model)

    def get_shop_categories(self, start_make=0, start_model=0, start_year=0):
        is_found_start_idx = False
        shop_categories = []
        
        if start_make == 0:
            is_found_start_idx = True
        
        #shop 옵션 값 가져오기
        make_select = Select(self.driver.find_element(By.ID, 'level1'))
        make_options = make_select.options
        make_options = make_options[1:]

        for make_option in make_options:
            make_select.select_by_visible_text(make_option.text)
            model_select = Select(self.driver.find_element(By.ID, 'level2'))
            model_options = model_select.options
            model_options = model_options[1:]
            WebDriverWait(self.driver, 10).until(EC.presence_of_all_elements_located((By.ID, 'level2')))

            for model_option in model_options:
                model_select.select_by_visible_text(model_option.text)
                year_select = Select(self.driver.find_element(By.ID, 'level3'))
                year_options = year_select.options
                year_options = year_options[1:]
                WebDriverWait(self.driver, 10).until(EC.presence_of_all_elements_located((By.ID, 'level3')))
                Util.wait_time(self.logger, 180)

                for year_option in year_options:
                    # if start_make == make_option.text and start_model == model_option.text and start_year == year_option.text and is_found_start_idx == False:
                    #     is_found_start_idx = True
                    #     self.logger.log(log_level="Event", log_msg=f"Start point found! : {make_option.text}, {model_option.text}, {year_option.text}")
                    
                    if is_found_start_idx:
                        self.logger.log(log_level="Debug", log_msg=f"Brand : {make_option.text}, Model : {model_option.text}, Year : {year_option.text}, Value : {year_option.get_attribute('value')}")
                        shop_category = ShopCatrgory(make=make_option.text, model=model_option.text, year=year_option.text, href=year_option.get_attribute("value"))
                        shop_categories.append(shop_category)

        return shop_categories

    def get_items_from_page(self, src):
        item_hrefs = []
        item_codes = []
        item_href = ""
        item_code = ""
        self.driver_manager.get_page(src)
        
        if self.driver_manager.is_element_exist(By.CLASS_NAME, "v-product"):
            item_elements = self.driver.find_elements(By.CLASS_NAME, "v-product")
            for item_element in item_elements:
                item_href = item_element.find_element(By.CLASS_NAME, "v-product__img").get_attribute("href")
                item_code = item_element.find_element(By.CLASS_NAME, "text.v-product__desc").text
                
                if "Part Number" in item_code:
                    item_code = item_code.split(":")
                    if len(item_code) == 1:
                        item_code = item_code[0][12:]
                    else:
                        item_code = item_code[1][1:]
                item_hrefs.append(item_href)
                item_codes.append(item_code)
        
        #테이블로 표현된 경우에는 5 tr 사용, 5 tr 당 3개의 상품
        if self.driver_manager.is_element_exist(By.XPATH, '//*[@id="MainForm"]/table[2]/tbody/tr/td/table/tbody/tr/td/table'):
            item_elements = self.driver.find_element(By.XPATH, '//*[@id="MainForm"]/table[2]/tbody/tr/td/table/tbody/tr/td/table').find_elements(By.TAG_NAME, "tr")
            for i in range(0, len(item_elements), 5):
                #1, 3 인덱스 사용
                item_href_elements = item_elements[1].find_elements(By.TAG_NAME, "td")
                item_code_elements = item_elements[3].find_elements(By.TAG_NAME, "td")
                
                for i in range(len(item_href_elements)):
                    item_href = item_href_elements[i].find_element(By.CLASS_NAME, "productnamecolor.colors_productname").get_attribute("href")
                    item_code = item_code_elements[i].text
                    
                    if "Part Number" in item_code:
                        item_code = item_code.split(":")
                        item_code = item_code[1][1:]
                    item_hrefs.append(item_href)
                    item_codes.append(item_code)

        return item_hrefs, item_codes

    def get_item_info(self, src, code, shop_catrgory, output_name):
        self.driver_manager.get_page(src)

        temp_code = code.replace(" ", "")
        item_code = f"tx_{temp_code}"
        item_code = item_code.replace("/", "-")
        item_model = f"{shop_catrgory.make} {shop_catrgory.model} {shop_catrgory.year}"

        item_name = self.driver.find_element(By.CLASS_NAME, 'vp-product-title').text
        org_price = self.driver.find_element(By.CLASS_NAME, 'product_productprice').text.split(":")
        org_price = org_price[1][2:]
        dealer_price = ""

        if self.driver_manager.is_element_exist(By.CLASS_NAME, 'product_saleprice'):
            dealer_price = self.driver.find_element(By.CLASS_NAME, 'product_saleprice').find_element(By.TAG_NAME, 'span').text
        else:
            dealer_price = org_price

        img_hrefs = []
        is_large_img_exist = False
        if self.driver_manager.is_element_exist(By.ID, "product_photo"):
            img_elemnet = self.driver.find_element(By.ID, "product_photo")
            img_hrefs.append(img_elemnet.get_attribute("src"))
            is_large_img_exist = True
        
        if self.driver_manager.is_element_exist(By.ID, "altviews"):
            if is_large_img_exist:
                img_hrefs.pop()
            img_elemnets = self.driver.find_element(By.ID, "altviews").find_elements(By.TAG_NAME, "a")
            for i in range(0, len(img_elemnets), 2):
                img_hrefs.append(img_elemnets[i].get_attribute("href"))
        img_hrefs = img_hrefs[0:12]
        
         #이미지 다운로드
        image_cnt = 1
        image_names = []
        for img_href in img_hrefs:
            image_name = f"{item_code}_{image_cnt}"
            self.driver_manager.download_image(img_href, image_name, f"./output/{output_name}/images", 0)
            image_names.append(image_name+".jpg")
            image_cnt += 1
        
        option_names = []
        options = []

        if self.driver_manager.is_element_exist(By.CLASS_NAME, "vol-option-name"):
            option_name_elements = self.driver.find_elements(By.CLASS_NAME, "vol-option-name")
            for option_name_element in option_name_elements:
                option_name = option_name_element.text
                option_names.append(option_name[:-2])

            option_elements = self.driver.find_elements(By.CLASS_NAME, "vol-option-items.vol-option-select")
            for option_element in option_elements:
                option_list = []
                option_selects = Select(option_element.find_element(By.TAG_NAME, "select")).options
                for option_select in option_selects:
                    if int(option_select.get_attribute("value")) != 0:
                        option_list.append(option_select.text)
                options.append(option_list)

        option_name = ""
        option_value = ""
        
        for name in option_names:
            option_name += name
            if name != option_names[-1]:
                option_name += "|"
        
        for option in options:
            for val in option:
                option_value += val
                if val != option[-1]:
                    option_value += ";"
            if option != options[-1]:
                    option_value += "|"

        item_description = ""
        if self.driver_manager.is_element_exist(By.ID, "product_description"):
            text_elements = self.driver.find_element(By.ID, "product_description").find_elements(By.TAG_NAME, "li")
            for text_element in text_elements:
                item_description += text_element.text
                item_description += "|"
            
            if self.driver_manager.is_element_exist(By.CSS_SELECTOR, "#product_description > div"):
                text = self.driver.find_element(By.ID, "product_description").find_element(By.TAG_NAME, "div").text
                item_description += text.replace("\n", "|")
            if self.driver_manager.is_element_exist(By.CSS_SELECTOR, "#product_description > span"):
                text = self.driver.find_element(By.CSS_SELECTOR, "#product_description > span").text
                item_description += text.replace("\n", "|")

        product = Product(code=item_code, name=item_name, price=org_price, dealer_price=dealer_price, description=item_description, 
                            trans_description=Util.translator(self.logger, "en", "ko", item_description), images=image_names, option_name=option_name, option_value=option_value, model=item_model)
        self.add_product_to_data(product)
        self.save_csv_datas(output_name=output_name)

        self.logger.log(log_level="Event", log_msg=f"Product \'{product.name}\' information crawling completed")
        return

    def save_csv_datas(self, output_name):
        data_frame = pd.DataFrame(self.data)
        data_frame.to_excel(f"./output/{output_name}/{output_name}.xlsx", index=False)
        return
    
    def start_crawling(self):
        now = datetime.datetime.now()
        year = f"{now.year}"
        month = "%02d" % now.month
        day = "%02d" % now.day
        output_name = f"{year+month+day}_MRA"
        
        self.file_manager.creat_dir(f"./output/{output_name}")
        self.file_manager.creat_dir(f"./output/{output_name}/images")
        
        id, pw, start_make, start_model, start_year = self.get_init_settings_from_file()
        
        self.driver_manager.get_page("https://www.mrashop.de/com/model-based-products/")

        try:
            shop_categories = self.get_shop_categories(start_make, start_model, start_year)
        except Exception as e:
            self.logger.log(log_level="Error", log_msg=f"Error in get_shop_categories : {e}")
            return
        
        for shop_catrgory in shop_categories:
            self.logger.log(log_level="Event", log_msg=f"Current maker : {shop_catrgory.make}, model : {shop_catrgory.model}, year : {shop_catrgory.year}")
            cat_num = shop_catrgory.href.split("/")
            cat_num = cat_num[-1]
            cat_num = cat_num[:4]
            category_href = f"{shop_catrgory.href}?searching=Y&sort=13&cat={cat_num}&show=300&page=1"
            self.driver_manager.get_page(category_href)
            last_page = 0
            if self.driver_manager.is_element_exist(By.XPATH, '//*[@id="MainForm"]/table[1]/tbody/tr/td/table[1]/tbody/tr[1]/td[2]/nobr/font/b/font/b'):
                last_page = self.driver.find_element(By.XPATH, '//*[@id="MainForm"]/table[1]/tbody/tr/td/table[1]/tbody/tr[1]/td[2]/nobr/font/b/font/b').text.split(" ")[2]
            item_hrefs = []
            item_codes = []
            for page in range(int(last_page)):
                category_href = f"{shop_catrgory.href}?searching=Y&sort=13&cat={cat_num}&show=300&page={page+1}"
                try:
                    temp_hrefs, temp_codes = self.get_items_from_page(category_href)
                except Exception as e:
                    self.logger.log(log_level="Error", log_msg=f"Error in get_items_from_page : {e}")
                    return
                item_hrefs += temp_hrefs
                item_codes += temp_codes

            for i in range(len(item_hrefs)):
                try:
                    item_info = self.get_item_info(item_hrefs[i], item_codes[i], shop_catrgory, output_name)
                except Exception as e:
                    self.logger.log(log_level="Error", log_msg=f"Error in get_item_info : {e}")
                    return

