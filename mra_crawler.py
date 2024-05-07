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
import logging


@dataclass
class Product:
    code: str
    name: str
    price: str
    length: str
    width: str
    shipment: str
    description: str
    trans_description: str
    images: list
    option_name: str
    option_value: str
    make: str
    model: str
    year: str

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
        self.driver_manager = DriverManager.WebDriverManager(self.logger, is_headless=False, is_use_udc=True)
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
        
        start_maker_val = 0
        start_model_val = 0
        start_year_val = 0
        end_maker_val = 0
        end_model_val = 0
        end_year_val = 0
        
        #cvs 파일에서 계정 정보, 브랜드, 브랜드 코드 가져오기
        data = pd.read_csv("./setting.csv").fillna(0)
        
        start_maker = data["start_maker"].to_list()
        start_maker.append(0)
        start_maker = start_maker[0:start_maker.index(0)]
        
        start_model = data["start_model"].to_list()
        start_model.append(0)
        start_model = start_model[0:start_model.index(0)]

        start_year = data["start_year"].to_list()
        start_year.append(0)
        start_year = start_year[0:start_year.index(0)]
        
        end_maker = data["end_maker"].to_list()
        end_maker.append(0)
        end_maker = end_maker[0:end_maker.index(0)]
        
        end_model = data["end_model"].to_list()
        end_model.append(0)
        end_model = end_model[0:end_model.index(0)]
        
        end_year = data["end_year"].to_list()
        end_year.append(0)
        end_year = end_year[0:end_year.index(0)]
        
        if len(start_maker) == 0:
            start_maker_val = 0
            start_model_val = 0
            start_year_val = 0
            
        if len(end_maker) == 0:
            end_maker_val = 0
            end_model_val = 0
            end_year_val = 0
        
        if not isinstance(start_year[0], str):
            if isinstance(start_year[0], int):
                start_maker_val = start_maker[0]
                start_model_val = start_model[0]
                start_year_val = str(start_year[0])
            elif isinstance(start_year[0], float):
                start_maker_val = start_maker[0]
                start_model_val = start_model[0]
                start_year_val = str(int(start_year[0]))
            else:
                start_maker_val = start_maker[0]
                start_model_val = start_model[0]
                start_year_val = start_year[0]
        else:
            start_maker_val = start_maker[0]
            start_model_val = start_model[0]
            start_year_val = start_year[0]
            
        if not isinstance(end_year[0], str):
            if isinstance(end_year[0], int):
                end_maker_val = end_maker[0]
                end_model_val = end_model[0]
                end_year_val = str(end_year[0])
            elif isinstance(end_year[0], float):
                end_maker_val = end_maker[0]
                end_model_val = end_model[0]
                end_year_val = str(int(end_year[0]))
            else:
                end_maker_val = end_maker[0]
                end_model_val = end_model[0]
                end_year_val = end_year[0]
        else:
            end_maker_val = end_maker[0]
            end_model_val = end_model[0]
            end_year_val = end_year[0]
            
        return start_maker_val, start_model_val, start_year_val, end_maker_val, end_model_val, end_year_val
        
    def data_init(self):
        self.data.clear()
        self.data["상품 코드"] = list()
        self.data["상품명"] = list()
        self.data["정상가"] = list()
        self.data["Length"] = list()
        self.data["Width"] = list()
        self.data["Shipment"] = list()
        self.data["설명"] = list()
        self.data["설명 번역"] = list()
        self.data["대표 이미지"] = list()
        self.data["상세 이미지"] = list()
        self.data["옵션명"] = list()
        self.data["옵션 내용"] = list()
        self.data["MAKE"] = list()
        self.data["MODEL"] = list()
        self.data["YEAR"] = list()
    
    def add_product_to_data(self, product):
        self.data["상품 코드"].append(product.code)
        self.data["상품명"].append(product.name)
        self.data["정상가"].append(product.price)
        
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
        self.data["Length"].append(product.length)
        self.data["Width"].append(product.width)
        self.data["Shipment"].append(product.shipment)
        self.data["설명"].append(product.description)
        self.data["설명 번역"].append(product.trans_description)
        self.data["MAKE"].append(product.make)
        self.data["MODEL"].append(product.model)
        self.data["YEAR"].append(product.year)

    def get_shop_categories(self, start_make=0, start_model=0, start_year=0, end_make=0, end_model=0, end_year=0):
        is_found_start_idx = False
        is_found_end_inx = False
        shop_categories = []
        
        if start_make == 0:
            is_found_start_idx = True
            
        if end_make == 0:
            is_found_end_inx = True
        
        #shop 옵션 값 가져오기
        WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.ID, 'level1')))
        make_select = Select(self.driver.find_element(By.ID, 'level1'))
        make_options = make_select.options
        make_options = make_options[1:]
        make_option_texts = [option.text for option in make_options]
        start_make_idx = 0

        if not is_found_start_idx:
            start_make_idx = make_option_texts.index(start_make)

        for i in range(start_make_idx, len(make_options)):
            WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.ID, 'level1')))
            make_select = Select(self.driver.find_element(By.ID, 'level1'))
            make_select.select_by_index(i+1)

            WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.ID, 'level2')))
            model_select = Select(self.driver.find_element(By.ID, 'level2'))

            model_options = model_select.options
            model_options = model_options[1:]
            model_option_texts = [option.text for option in model_options]
            start_model_idx = 0

            if not is_found_start_idx:
                start_model_idx = model_option_texts.index(start_model)

            for j in range(start_model_idx, len(model_options)):

                WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.ID, 'level2')))
                model_select = Select(self.driver.find_element(By.ID, 'level2'))
                model_select.select_by_index(j+1)
                Util.wait_time(logger=self.logger, wait_time=2)
                #WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.ID, 'level3')))
                if self.driver_manager.is_element_exist(By.ID, 'level3'):
                    year_select = Select(self.driver.find_element(By.ID, 'level3'))
                    year_options = year_select.options
                    year_options = year_options[1:]
                    year_option_texts = [option.text for option in year_options]
                    start_year_idx = 0

                    if not is_found_start_idx:
                        start_year_idx = year_option_texts.index(start_year)
                else:
                    year_options = []

                for k in range(len(year_options)):
                    year_option = year_options[k]
                    if start_make == make_option_texts[i] and start_model == model_option_texts[j] and start_year == year_option_texts[k] and is_found_start_idx == False:
                        is_found_start_idx = True
                        self.logger.log(log_level="Event", log_msg=f"Start point found! - Brand : {make_option_texts[i]}, Model : {model_option_texts[j]}, Year : {year_option_texts[k]}")
                    
                    if is_found_start_idx:
                        self.logger.log(log_level="Event", log_msg=f"Brand : {make_option_texts[i]}, Model : {model_option_texts[j]}, Year : {year_option_texts[k]}, Value : {year_option.get_attribute('value')}")
                        shop_category = ShopCatrgory(make=make_option_texts[i], model=model_option_texts[j], year=year_option_texts[k], href=year_option.get_attribute("value"))
                        shop_categories.append(shop_category)
                        if end_make == make_option_texts[i] and end_model == model_option_texts[j] and end_year == year_option_texts[k] and is_found_end_inx == False:
                            self.logger.log(log_level="Event", log_msg=f"End point found! - Brand : {make_option_texts[i]}, Model : {model_option_texts[j]}, Year : {year_option_texts[k]}")
                            return shop_categories

        return shop_categories

    def get_items_from_page(self, src):
        item_hrefs = []
        is_last_page = False
        page = 1
        while(not is_last_page):
            page_url = f"{src}?p={page}"
            self.driver_manager.get_page(page_url)
            
            if self.driver_manager.is_element_exist(By.CLASS_NAME, "product--info"):
                product_elements = self.driver.find_elements(By.CLASS_NAME, "product--info")
                for product_element in product_elements:
                    href = product_element.find_element(By.TAG_NAME, "a").get_attribute("href")
                    item_hrefs.append(href)
            else:
                is_last_page = True
            page += 1

        return item_hrefs

    def get_item_info(self, src, shop_catrgory, output_name):
        is_page_loaded = self.driver_manager.get_page(src)
        
        if is_page_loaded:
            item_name = self.driver.find_element(By.CLASS_NAME, 'product--title').text
            org_price = self.driver.find_element(By.CLASS_NAME, 'product--price.price--default').find_element(By.TAG_NAME, "meta").get_attribute("content")
            
            item_code = "mra-"
            item_length = ""
            item_width = ""
            item_shipment = ""
            
            if self.driver_manager.is_element_exist(By.CLASS_NAME, "product--base-info.list--unstyled"):
                product_info_list = self.driver.find_element(By.CLASS_NAME, "product--base-info.list--unstyled")
                product_info_elements = product_info_list.find_elements(By.TAG_NAME, "li")
                product_info_elements = product_info_elements[1:]
                
                for product_info_element in product_info_elements:
                    text = product_info_element.find_element(By.CLASS_NAME, "entry--content").text
                    lable = product_info_element.find_element(By.CLASS_NAME, "entry--label").text
                    if "Order number" in lable:
                        item_code += text
                    elif "Length" in lable:
                        item_length = text
                    elif "Width" in lable:
                        item_width = text
                    elif "Shipment" in lable:
                        item_shipment = text
                    
            img_hrefs = []
            
            if self.driver_manager.is_element_exist(By.CLASS_NAME, "image--box.image-slider--item.image-slider--item--image"):
                img_elements = self.driver.find_elements(By.CLASS_NAME, "image--box.image-slider--item.image-slider--item--image")
                for img_element in img_elements:
                    img_href = img_element.find_element(By.CLASS_NAME, "image--element").get_attribute("data-img-original")
                    img_hrefs.append(img_href)
            
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

            if self.driver_manager.is_element_exist(By.CLASS_NAME, "product--configurator"):
                option_name_elements = self.driver.find_element(By.CLASS_NAME, "product--configurator").find_elements(By.CLASS_NAME, "configurator--label")
                for option_name_element in option_name_elements:
                    option_name = option_name_element.text
                    option_names.append(option_name[:-1])

                option_elements = self.driver.find_element(By.CLASS_NAME, "product--configurator").find_elements(By.TAG_NAME, "select")
                for option_element in option_elements:
                    option_list = []
                    option_selects = Select(option_element).options
                    for option_select in option_selects:
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
            if self.driver_manager.is_element_exist(By.CLASS_NAME, "product--description"):
                item_description = self.driver.find_element(By.CLASS_NAME, "product--description").text.replace("\n", "|")
                if not isinstance(item_description, str):
                    item_description = ""

            product = Product(code=item_code, name=item_name, price=org_price, length=item_length, width=item_width, shipment=item_shipment, description=item_description, 
                                trans_description=Util.translator(self.logger, "en", "ko", item_description), images=image_names, option_name=option_name, 
                                option_value=option_value, make=shop_catrgory.make, model=shop_catrgory.model, year=shop_catrgory.year)

            self.add_product_to_data(product)
            self.save_csv_datas(output_name=output_name)

            self.logger.log(log_level="Event", log_msg=f"Product \'{product.name}\' information crawling completed")
        else:
            product = Product(code=src, name="", price="", length="", width="", shipment="", description="", 
                                trans_description="", images="", option_name="", option_value="", make=shop_catrgory.make, model=shop_catrgory.model, year=shop_catrgory.year)

            self.add_product_to_data(product)
            self.save_csv_datas(output_name=output_name)

            self.logger.log(log_level="Event", log_msg=f"Product \'{product.name}\' information crawling failed")
        return
    
    def get_item_info_with_bs(self, src, shop_catrgory, output_name):
        soup = self.driver_manager.get_bs_soup(src)
        
        item_model = f"{shop_catrgory.make} {shop_catrgory.model} {shop_catrgory.year}"
        item_name = soup.select_one('.product--title').get_text().replace('\n', "")
        org_price = soup.select_one('body > div > section > div > div.content--wrapper > div > div.product--detail-upper.block-group > div.product--buybox.block > div > div.product--price.price--default > span > meta').attrs["content"]
        
        item_code = "mra-"
        item_length = ""
        item_width = ""
        item_shipment = ""
        
        if soup.select("body > div > section > div > div.content--wrapper > div > div.product--detail-upper.block-group > div.product--buybox.block > ul > li") is not None:
            product_info_elements = soup.select("body > div > section > div > div.content--wrapper > div > div.product--detail-upper.block-group > div.product--buybox.block > ul > li")
            product_info_elements = product_info_elements[1:]
            
            for product_info_element in product_info_elements:
                text = product_info_element.select_one("span").get_text().replace('\n', "")
                lable = product_info_element.select_one("strong").get_text().replace('\n', "")
                if "Order number" in lable:
                    item_code += text
                elif "Length" in lable:
                    item_length = text
                elif "Width" in lable:
                    item_width = text
                elif "Shipment" in lable:
                    item_shipment = text
                
        img_hrefs = []
        
        if soup.select("body > div > section > div > div.content--wrapper > div > div.product--detail-upper.block-group > div.product--image-container.image-slider.product--image-zoom > div.image-slider--container > div > div > span") is not None:
            img_elements = soup.select("body > div > section > div > div.content--wrapper > div > div.product--detail-upper.block-group > div.product--image-container.image-slider.product--image-zoom > div.image-slider--container > div > div > span")
            print(img_elements)
            for img_element in img_elements:
                img_href = img_element.attrs["data-img-original"]
                img_hrefs.append(img_href)
        
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

        if soup.select("body > div > section > div > div.content--wrapper > div > div.product--detail-upper.block-group > div.product--buybox.block > div > div.product--configurator > form > p") is not None:
            option_name_elements = soup.select("body > div > section > div > div.content--wrapper > div > div.product--detail-upper.block-group > div.product--buybox.block > div > div.product--configurator > form > p")
            for option_name_element in option_name_elements:
                option_name = option_name_element.get_text()
                option_names.append(option_name[:-1])

            option_elements = soup.select("body > div > section > div > div.content--wrapper > div > div.product--detail-upper.block-group > div.product--buybox.block > div > div.product--configurator > form > div > select")
            for option_element in option_elements:
                option_list = []
                option_selects = option_element.select("option")
                for option_select in option_selects:
                    option_list.append(option_select.get_text().replace('\n', ""))
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
        if soup.select(".product--description") is not None:
            item_description = soup.select_one(".product--description").get_text().replace("\n", "|")
            if not isinstance(item_description, str):
                item_description = ""

        product = Product(code=item_code, name=item_name, price=org_price, length=item_length, width=item_width, shipment=item_shipment, description=item_description, 
                            trans_description=Util.translator(self.logger, "en", "ko", item_description), images=image_names, option_name=option_name, 
                            option_value=option_value, make=shop_catrgory.make, model=shop_catrgory.model, year=shop_catrgory.year)

        print(product)
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

        start_make, start_model, start_year, end_make, end_model, end_year = self.get_init_settings_from_file()
        
        self.driver_manager.get_page("https://www.mrashop.de/com/model-based-products/")

        try:
            shop_categories = self.get_shop_categories(start_make, start_model, start_year, end_make, end_model, end_year)
        except Exception as e:
            self.logger.log(log_level="Error", log_msg=f"Error in get_shop_categories : {e}")
            return
        
        for shop_catrgory in shop_categories:
            item_hrefs = []
            
            self.logger.log(log_level="Event", log_msg=f"Current maker : {shop_catrgory.make}, model : {shop_catrgory.model}, year : {shop_catrgory.year}")
            try:
                item_hrefs = self.get_items_from_page(shop_catrgory.href)
            except Exception as e:
                self.logger.log(log_level="Error", log_msg=f"Error in get_items_from_page : {e}")
                return

            for item_href in item_hrefs:
                try:
                    item_info = self.get_item_info(item_href, shop_catrgory, output_name)
                except Exception as e:
                    self.logger.log(log_level="Error", log_msg=f"Error in get_item_info : {e}")
                    return

