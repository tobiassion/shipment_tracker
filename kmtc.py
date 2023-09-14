# request API
import requests

# loading data from Gsheet
from io import BytesIO

# parsing data
import pandas as pd
from datetime import date
from datetime import datetime
from dateutil.parser import parse

# looping progress
from tqdm import tqdm

# connect to mongodb
import pymongo
from pymongo import MongoClient
from pymongo.server_api import ServerApi

# class to date or not
def is_date(string, fuzzy=False):
    try: 
        parse(string, fuzzy=fuzzy)
        return True
    except ValueError:
        return False

# reading all BL number from google sheet
r = requests.get('https://docs.google.com/spreadsheets/d/e/2PACX-1vTAFNFtEXE7yWMYbkJF81On78NhnYpQisqdDbhvW4aPjPYuSMLVSrIDuIK5D6zY0cS9kboGaFazqL3e/pub?output=csv')
data = r.content
df = pd.read_csv(BytesIO(data))
liners_bl = df[df["LINERS"] == "KMTC"]
bl_list = list(set(liners_bl["BL Number"]))

failed = []

hasil_akhir = []
for i, bls in enumerate(tqdm(bl_list)):
    try:
        # hitting the API
        url_ctr = "https://api.ekmtc.com/trans/trans/cargo-tracking/{}?dtKnd=BL&blNo={}".format(
            bls[4:], bls[4:])
        response_ctr = requests.request("GET", url_ctr)

        # getting container data. booking id needed for API URL
        ctr_data = response_ctr.json()
        list_of_container_number = []
        list_of_bookingid = []

        for j, ctr_info in enumerate(ctr_data['cntrList']):
            list_of_container_number.append(ctr_info["cntrNo"])
            list_of_bookingid.append(ctr_info["bkgNo"])

        for c, ctr in enumerate(list_of_container_number):
            url_milestone = "https://api.ekmtc.com/trans/trans/cargo-tracking/{}/detail?bkgNo={}&cntrNo={}&dtKnd=BL&strBkgNo={}".format(
                bls[4:], list_of_bookingid[c], ctr, list_of_bookingid[c])
            
            # hitting the API again for every container for container milestones
            response_milestone = requests.request("GET", url_milestone)

            # aqcuiring milestone datas for every container
            milstone_data = response_milestone.json()
            current_dict = {}
            dict_milestone = {}
            milestones = []
            key_mapping = {
                'blNo': 'BL Number',
                'cntrNo': 'Container Number',
                'etd': 'ETD',
                'eta': 'ETA',
                # 'GTOOB':'Gate Out Origin',
                # 'GTIOB':'Gate In Origin',
                'LDGOB': 'ATD',
                'DISIB': 'ATA',
                'GTOIB': 'Container Release',
                'GTIIB': 'Container Return'
            }

            current_dict.update({"Liners": "KMTC"})
            current_dict.update(
                {"From": milstone_data['trackingList'][-1]['plcNm'][:milstone_data['trackingList'][-1]['plcNm'].index(",")]})
            current_dict.update(
                {"To": milstone_data['trackingList'][-1]['podPortNm']})

            for key, label in key_mapping.items():
                if key in ctr_data['cntrList'][c]:
                    if key == "etd" or key == "eta":
                        current_dict[label] = datetime.strptime(
                            ctr_data['cntrList'][c][key][:8], "%Y%m%d").strftime("%Y-%m-%d")
                    else:
                        current_dict[label] = ctr_data['cntrList'][c][key]

            for b, milestone in enumerate(milstone_data['trackingList']):
                milestones.append(
                    milestone["cntrStsCd"] + milestone["cntrMvntCd"])
                milestones.append(milestone["mvntDt"])

            for m, milestone in enumerate(milestones):
                if is_date(milestone):
                    case_milestone = {
                        milestones[m-1]: datetime.strptime(milestone, "%Y%m%d").strftime("%Y-%m-%d")}
                    dict_milestone.update(case_milestone)

            for key, label in key_mapping.items():
                if key in dict_milestone:
                    current_dict[label] = dict_milestone[key]

            print(current_dict)
            hasil_akhir.append(current_dict)
    except Exception as e:
        print(e)
        print("{} GAGAL!!".format(bls))
        failed.append(bls)

# connect to mongodb
from pymongo import MongoClient

cluster = MongoClient("mongodb+srv://tobiassion:tobiassion@cluster0.u2vzz3d.mongodb.net/?retryWrites=true&w=majority")
db = cluster["bl_tracking"]
collection = db["testing-server-debian"]
collection.insert_many(hasil_akhir)
print("inserting many complete!!")


# connect to mongodb
from pymongo import MongoClient

# Provide the connection details
hostname = '10.1.201.71'
port = 27017  # Default MongoDB port
username = ''  # If authentication is required
password = ''  # If authentication is required

# Create a MongoClient instance
client = MongoClient(hostname, port, username=username, password=password)

db = client["stockcontroll"]
print(db)
collection = db["testing-server-debian"]
collection.insert_many(hasil_akhir)
print("inserting many complete!!")
