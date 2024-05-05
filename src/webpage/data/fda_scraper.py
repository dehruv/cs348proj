import requests
import pandas as pd
from datetime import datetime

url = "https://www.accessdata.fda.gov/scripts/drugshortages/Drugshortages.cfm"
response = requests.get(url)

if response.status_code == 200:
    df = pd.read_csv("fulltable")
    last_median = df["Payment Limit"].median()
    consts = open("consts.txt", "w")
    consts.write(str(last_median))
    consts.close()
    with open('shortages.csv', 'wb') as f:
        f.write(response.content)
else:
    print("File not downloaded successfully")
