import sqlite3
import pandas as pd
from sqlalchemy import create_engine


con = sqlite3.connect("shortages.db")
cur = con.cursor()

df = pd.read_csv("data/fulltable")
e = create_engine('sqlite://')
df.to_sql('shortages', con, if_exists="replace")

