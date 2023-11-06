import pandas as pd
import requests
from io import BytesIO
import datetime

# initiating mongo
from pymongo import MongoClient
from datetime import date
def delete_all():
    hostname = '10.1.201.71:27017'
    port = 27017
    username = ''
    password = ''
    cluster = MongoClient(hostname, port, username=username, password=password)

    collection_name = "fototiers"

    db = cluster["stockcontroll"]
    collection = db[collection_name]
    collection.delete_many({})
    return print("All data cleared!!")

def insert_many_mongo(results):
    hostname = '10.1.201.71:27017'
    port = 27017
    username = ''
    password = ''
    cluster = MongoClient(hostname, port, username=username, password=password)

    collection_name = "fototiers"

    db = cluster["stockcontroll"]
    collection = db[collection_name]
    collection.insert_many(results)
    return print("Inserting Many Complete!!")

# exporting spreadsheet
r = requests.get('https://docs.google.com/spreadsheets/d/e/2PACX-1vRFmFhaTbD3Yv-R8Hrvu7QBmbNGyY2UzZtg4ICWBArbAlcZ0ogNr3TPbO0740GgqXOYx9e4IlEKNplP/pub?output=csv')
df = pd.read_csv(BytesIO(r.content))

# deleting unamed columns
columns_to_keep = [col for col in df.columns if 'Unnamed' not in col]
df = df[columns_to_keep]

# dropping unwanted columns
index_column_to_drop = [1,2,3]
df = df.drop(df.columns[index_column_to_drop], axis=1)
df['Nomor Shipment'] = df['Nomor Shipment'].astype(str)

# change df to list of dict
dict_of_data = df.to_dict('records')

# looping through list of dicts
# 1. using mongodb format
# 2. deleting nan
# 3. change 'Upload Foto Tier ..' to 'TIER ..'
# 4. appending to list of dict to upload to mongo 

data_to_upload = []
for i, dicts in enumerate(dict_of_data):
    merged_upload = {}
    upload_photos = []
    for key, value in dicts.items():
        if 'Upload Foto Tier' in key:
            text = str(key)
            last_space_index = text.rfind(' ')  
            if last_space_index != -1:  
                sliced_text = text[last_space_index + 1:]  
            else:
                print("No space found in the text")
            case = {"Nama" : "TIER " + sliced_text, "URL" : str(value)}
        
            if case["URL"] != 'nan':
                upload_photos.append(case)
        else:
            if str(value) == 'nan':
                merged_upload[key.replace(" ", "_")] = ""
            else:
                merged_upload[key.replace(" ", "_")] = value
        merged_upload['Upload_Photos'] = upload_photos

    case_date1 = {"createdAt":int(datetime.datetime.timestamp(datetime.datetime.strptime(merged_upload["Timestamp"], "%d/%m/%Y %H:%M:%S")))}
    case_date2 = {"updatedAt":int(datetime.datetime.timestamp(datetime.datetime.strptime(merged_upload["Timestamp"], "%d/%m/%Y %H:%M:%S")))}
    merged_upload.update(case_date1)
    merged_upload.update(case_date2)

    data_to_upload.append(merged_upload)
# deleting all data in collection
delete_all()

# uploading list of dictionary to mongo
insert_many_mongo(data_to_upload)



