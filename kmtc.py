# parsing data from excel
import pandas as pd

# connect to mongodb
from pymongo import MongoClient

# sleep
import time

# isdate
from dateutil.parser import parse

# selenium
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
import undetected_chromedriver as uc

# looping process monitoring
from tqdm import tqdm

penampung = []
hasil = {}
gagal = []
final_bl = []

# set up connection with mongodb collection
cluster = MongoClient("mongodb+srv://tobiassion:tobiassion@cluster0.u2vzz3d.mongodb.net/?retryWrites=true&w=majority")
db = cluster["bl_tracking"]
collection = db["bl_track_fix"]

# class to determine ganjil genap
def is_date(string, fuzzy=False):
    try: 
        parse(string, fuzzy=fuzzy)
        return True
    except ValueError:
        return False
    
df = pd.read_excel('BL Number EVGL.xlsx') 
parse_bl = df['BL Number'].tolist()
bl_list = list(set(list(parse_bl)))
bl_list = [x.strip(' ') for x in bl_list]

# slicer
s = slice(10)

# web scripting
options = Options()
options.add_argument("--window-size=1920,1280")
driver = uc.Chrome(use_subprocess=True)
driver.get("https://www.ekmtc.com/index.html#/main")

# click shipment tracker
click_cargo_tracking = driver.find_element(By.XPATH, "/html/body/div/div[1]/div[2]/body/div/div[2]/div[2]/div[1]/form/div/div[2]/div/a")
click_cargo_tracking.click()

# inputing BL Number
BL_input = driver.find_element(By.XPATH, "/html/body/div[1]/div[1]/div[2]/body/div/div[2]/div[2]/div[1]/form/div/div[2]/div/div/p/span/input")
BL_input.send_keys(bl_list[0])

# click search
click_search = driver.find_element(By.XPATH, "/html/body/div[1]/div[1]/div[2]/body/div/div[2]/div[2]/div[1]/form/div/div[2]/div/div/a")
click_search.click()

time.sleep(1)

for i, bls in enumerate(tqdm(bl_list)):
    try:
        time.sleep(1)
        # input bl2
        wait_input = WebDriverWait(driver, 10).until(EC.presence_of_all_elements_located((By.XPATH, '/html/body/div/div[1]/div[2]/div[1]/form/div[1]/table/tbody/tr/td[2]/input')))
        BL_input2 = driver.find_element(By.XPATH, '/html/body/div/div[1]/div[2]/div[1]/form/div[1]/table/tbody/tr/td[2]/input')
        BL_input2.clear()
        BL_input2.send_keys(bls)

        time.sleep(1)

        # clik submit
        submit_button = driver.find_element(By.LINK_TEXT,'Search')
        driver.execute_script("arguments[0].click();", submit_button)

        # data scraping
        data_table = WebDriverWait(driver, 10).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="frm"]//ul[@class="location_detail"]//div[@class="ts_scroll"]/div/p')))

        #input BL Number to Dictionary
        hasil.update({"BL Number" : bls})
        
        for i, item in enumerate(data_table):
            info = item.text
            tulis = info.replace("\n", " ")
            penampung.append(tulis)
        penampung = list(filter(None, penampung))
        
        for j,item in enumerate(penampung):
            if(is_date(item)):
                case={penampung[j-1]:item[s]}
                hasil.update(case)
     
        # appending bl details to db
        final_bl.append(hasil)
        hasil={}
        print(bls, "\n done listed")

    except Exception as e:
        print("An unexpected error occurred: {} cant bre processed".format(bls))
        gagal.append(bls)
    finally:
        pass

collection.insert_many(final_bl)
print("inserting many complete!!")
print(gagal)
driver.close