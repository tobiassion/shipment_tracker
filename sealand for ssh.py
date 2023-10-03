# request
import requests

# io
from io import BytesIO

# web scraper
from bs4 import BeautifulSoup

# date parser and sleep
from dateutil.parser import parse
import time

# web driver
from datetime import datetime
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
import undetected_chromedriver as uc

# reeading and exporting to excel files
import pandas as pd

# looping process monitoring
from tqdm import tqdm
import random

# initiating mongo
from pymongo import MongoClient
from datetime import date

# initiating new mongo db
def mongo_table_initiation():

    # date time today
    today = date.today()
    date_today = today.strftime("%b-%d-%Y")

    # name of collection to store tracking results
    dbname = "all_tracking_" + date_today
    initiator = {
        "Liners":"XXXX",
        "BL Number":"XXXX",
        "Container Number":"XXXX",
        "From":"XXXX",
        "To":"XXXX",
        "ETD":"XXXX",
        "ETA":"XXXX",
        "ATD":"XXXX",
        "ATA":"XXXX",
        "Container Release":"XXXX",
        "Container Return":"XXXX",
    }

    # finding name 
    cluster = MongoClient("mongodb+srv://tobiassion:tobiassion@cluster0.u2vzz3d.mongodb.net/?retryWrites=true&w=majority")
    db = cluster["bl_tracking"]
    print("Today's Collection Name ===> ", dbname)
    if dbname in db.list_collection_names():
        return print("Today's Collection Has Been Made")
    else:
        collection = db[dbname]
        collection.insert_one(initiator)
        return print("Table initiation complete")

def insert_many_mongo(results):
    # today's date
    today = date.today()
    date_today = today.strftime("%b-%d-%Y")
    collection_name = "all_tracking_" + date_today

    cluster = MongoClient("mongodb://10.1.201.71:27017/?compressors=none&authMechanism=DEFAULT")
    db = cluster["tobias"]
    collection = db[collection_name]
    collection.insert_many(results)
    return print("Inserting Many Complete!!")

# class to determine date or not
def is_date(string, fuzzy=False):
    try: 
        parse(string, fuzzy=fuzzy)
        return True
    except ValueError:
        return False

s = slice(11)

# reading all BL number from google sheet
import pandas as pd
r = requests.get('https://docs.google.com/spreadsheets/d/e/2PACX-1vTAFNFtEXE7yWMYbkJF81On78NhnYpQisqdDbhvW4aPjPYuSMLVSrIDuIK5D6zY0cS9kboGaFazqL3e/pub?output=csv')
data = r.content
df = pd.read_csv(BytesIO(data))
liners_bl = df[df["LINERS"] == "SEALAND"]
bl_list = list(set(liners_bl["BL Number"]))


dict_hasil = {}
current_dict = {}
list_dict = []
gagal = []

list_dict = []
# web scripting
options = Options()
options.add_argument("--window-size=1920,1280")
driver = uc.Chrome(use_subprocess=True)
driver.get('https://www.sealandmaersk.com/tracking/' + bl_list[random.randint(0, len(bl_list)-1)])

# wait to load all
time.sleep(2)

#click allow all
click_allowall = driver.find_element(By.XPATH,'//button[text()="Allow all"]')
click_allowall.click()

# click asia
click_asia = driver.find_element(By.XPATH,"/html/body/div[2]/div/section/div/div[2]/form/div[1]/div/div/ol/li[3]/label/div[1]")
click_asia.click()

# click continue
click_continue = driver.find_element(By.ID,'confirmRegion')
click_continue.click()

for i, bls in enumerate(tqdm(bl_list)):
    try:
        # access the web
        driver.get('https://www.sealandmaersk.com/tracking/' + bl_list[i])

        # sleep wait
        time.sleep(3)
        
        # finding how many hide details in 1 page refering to how many container number in 1 bl
        soup1 = BeautifulSoup(driver.page_source, 'lxml')
        containers = soup1.find_all('div', {"data-test": "container"})
        number_of_ctr = len(containers)
        
        print(bls, "HAVE ", number_of_ctr, " CTR")
        # print(dict_hasil)

        # print("current bl: ", bls, "\n number of container: ", number_of_ctr)
        if number_of_ctr > 1:
            # taking BL Number, From, and To 
            title = driver.find_element(By.XPATH, "/html/body/main/div/div/dl")
            titles = title.text.split('\n')
            titles.remove('View Shipment Details')
            print(titles)
            for a, item in enumerate(titles):
                #
                if a%2==0 :
                    case_judul = {titles[a]:titles[a+1]}
                    dict_hasil.update(case_judul)
            
            print("Hasil dari Append Judul")
            print(dict_hasil)
            x=3
            # clicking all view more
            for c in range(number_of_ctr):
                try:
                    print("clicking div no :",  x)
                    show_details2 = WebDriverWait(driver, 30).until(EC.element_to_be_clickable((By.XPATH, '/html/body/main/div/div/div[{}]/dl/button'.format(x))))  
                    show_details2.click()
                    time.sleep(1)
                except Exception as e:
                    print(e)
                x=x+1

            time.sleep(2)
            # taking the whole page's html
            soup2 = BeautifulSoup(driver.page_source, 'lxml')
            
            table = soup2.find_all('div', {"data-test": "container"})
            milestones = []
            for tag in table:
                for ctri1, ctr_num1  in enumerate(tag.find_all('strong', {"data-test":'container-details-value'})):
                    temp_ctr_num1 = ctr_num1
                    milestones.append("Container Number")
                    milestones.append(temp_ctr_num1.text)
                for m, li_milestone in enumerate(tag.find_all('li', {"data-test":'transport-plan-item-complete'})):
                    span_history = li_milestone.find_all("span")
                    for c1, city1 in enumerate(li_milestone.find_all("strong")):
                        temp1 = city1.text
                    for milestone_span in span_history:
                        if is_date(milestone_span.text):
                            milestones.append(milestone_span.text[s])
                        else:
                            milestones.append(temp1 +" "+ milestone_span.text)
                            
                for n, li_expected in enumerate(tag.find_all('li', {"data-test":'transport-plan-item-future'})):
                    spans = li_expected.find_all("span")
                    for c2, city2 in enumerate(li_expected.find_all("strong")):
                        temp2 = city2.text
                    for expected_span in spans:
                        if is_date(expected_span.text):
                            milestones.append(expected_span.text[s])
                        else:
                            milestones.append(temp2 + " ESTIMATED " + expected_span.text)
                 
                for panjang in range(0, len(milestones), 2):
                    key = milestones[panjang]
                    value = milestones[panjang + 1]

                    if key == 'Container Number':
                        if current_dict:
                            list_dict.append(current_dict.copy())
                        current_dict = {'Container Number': value}
                    else:
                        current_dict[key] = value

                    current_dict.update(dict_hasil) 
                print(current_dict)
            list_dict.append(current_dict)
            current_dict = {}
            dict_hasil={}
            print(bls, ", completed!!")
        else:
            time.sleep(1)
            
            title = driver.find_element(By.XPATH, "/html/body/main/div/div/dl")
            titles = title.text.split('\n')
            titles.remove('View Shipment Details')
            for a, item in enumerate(titles):
                if a%2==0 :
                    case_judul = {titles[a]:titles[a+1]}
                    dict_hasil.update(case_judul)
            
            time.sleep(2)
            soup2 = BeautifulSoup(driver.page_source, 'lxml')
            
            table = soup2.find_all('div', {"data-test": "container"})
            milestones = []
            for tag in table:
                for ctri1, ctr_num1  in enumerate(tag.find_all('strong', {"data-test":'container-details-value'})):
                    temp_ctr_num1 = ctr_num1
                    milestones.append("Container Number")
                    milestones.append(temp_ctr_num1.text)

                for m, li_milestone in enumerate(tag.find_all('li', {"data-test":'transport-plan-item-complete'})):
                    span_history = li_milestone.find_all("span")
                    for c1, city1 in enumerate(li_milestone.find_all("strong")):
                        temp1 = city1.text
                    for milestone_span in span_history:
                        if is_date(milestone_span.text):
                            milestones.append(milestone_span.text[s])
                        else:
                            milestones.append(temp1 +" "+ milestone_span.text)
                            
                for n, li_expected in enumerate(tag.find_all('li', {"data-test":'transport-plan-item-future'})):
                    spans = li_expected.find_all("span")
                    for c2, city2 in enumerate(li_expected.find_all("strong")):
                        temp2 = city2.text
                    for expected_span in spans:
                        if is_date(expected_span.text):
                            milestones.append(expected_span.text[s])
                        else:
                            milestones.append(temp2 + " ESTIMATED " + expected_span.text)
            
            for t, milestone in enumerate(milestones):
                if milestone == "Container Number":
                    case_mlstn = {milestones[t]:milestones[t+1]}
                    current_dict.update(case_mlstn)
                elif t%2==0 :
                    case_mlstn = {milestones[t]:milestones[t+1]}
                    current_dict.update(case_mlstn)
                    
            current_dict.update(dict_hasil) 
            list_dict.append(current_dict)
            current_dict = {}
            dict_hasil={}
        
        unique_list = []
        for d in list_dict:
            if d not in unique_list:
                unique_list.append(d)

    except Exception as e:
        print(e)
        print("{} GAGAL!!".format(bls))
        gagal.append(bls)

filtered_dict_list =[]
for dict_milestone in unique_list:
    # print(dict_milestone)
    kw = ['Bill of Lading number', 'Container Number', 'From', 'To', dict_milestone['From'], dict_milestone['To']]
    dict_key = []
    for keys in dict_milestone:
        dict_key.append(keys)
    # print("BEFORE", dict_key)
    new_list = [] 
    
    for key in dict_key:
        if any(substring in key for substring in kw):
            new_list.append(key)
    # print("AFTER",new_list)
    dict_milestone = {key: dict_milestone[key] for key in new_list}
    filtered_dict_list.append(dict_milestone)

list_of_dict_fix = []
for filter_dict in filtered_dict_list:
    replacement_mapping = {
        filter_dict["From"]: 'Origin',
        filter_dict["To"]: 'Destination'
    }

    updated_dict = {}

    for key, value in filter_dict.items():
        for old_key, new_key in replacement_mapping.items():
            key = key.replace(old_key, new_key)
        updated_dict[key] = value

    list_of_dict_fix.append(updated_dict)


list_of_dict_fix2 = []
for filter_dict in list_of_dict_fix:
    replacement_mapping = {
        "Bill of Lading number" : "BL Number",
        "Origin Vessel departure": 'ATD',
        "Destination Discharge": 'ATA',
        "Destination Gate out": 'Container Release',
        "Destination Empty container return" : 'Container Return'
    }

    updated_dict = {}

    for key, value in filter_dict.items():
        for old_key, new_key in replacement_mapping.items():
            key = key.replace(old_key, new_key)
        updated_dict[key] = value

        if is_date(value):
           input_date = datetime.strptime(value, '%d %b %Y')
           updated_dict[key] = input_date.strftime("%Y-%m-%d")
    
    updated_dict["Liners"] = "SEALAND"

    list_of_dict_fix2.append(updated_dict)

# inserting to mongo from ssh
mongo_table_initiation()
insert_many_mongo(list_of_dict_fix2)