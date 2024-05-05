import pandas as pd
import numpy as np


in_shortage = pd.read_csv('shortages.csv')
in_shortage["NDC_id"] = in_shortage[" Presentation"].str.extract(
    r'\(NDC\s*(\S+)\)')  # primary key
code_split = in_shortage["NDC_id"].str.split("-")
code_split = code_split.apply(lambda x: [len(item) for item in x])

in_shortage["ndc type"] = code_split.apply(lambda x: "-".join(map(str, x)))

in_shortage["parsed_NDC_id"] = np.select(
    [
        in_shortage["ndc type"] == "5-3-2",
        in_shortage["ndc type"] == "4-4-2",
        in_shortage["ndc type"] == "5-4-1"
    ],
    [
        in_shortage["NDC_id"].str[:6] + "0" + in_shortage["NDC_id"].str[6:],
        "0" + in_shortage["NDC_id"],
        in_shortage["NDC_id"].str[:11] + "0" + in_shortage["NDC_id"].str[11:]
    ]
)

hcpcs_to_ndc = pd.read_excel('crosswalk.xlsx')
hcpcs_to_ndc.drop(columns=["NDC Mod"], inplace=True)

main = pd.merge(in_shortage, hcpcs_to_ndc, left_on="parsed_NDC_id",
                right_on="NDC", how="left", suffixes=('_yup', '_xtalk'))
main['HCPCS'] = main['HCPCS'].fillna(0)
valid_main = main[main["HCPCS"] != 0]

columns_to_drop = [' Generic Name Note',
                   ' Generic Name Link ',
                   ' Company Info Link',
                   ' Availability Link',
                   ' Related Info Link',
                   '   Resolved Note Link',
                   ' Discontinued Note Link',
                   'NDC_id',
                   'ndc type',
                   'parsed_NDC_id']
simplified_main = valid_main.drop(columns=columns_to_drop)

prices = pd.read_excel("price.xls")
prices = prices.iloc[7:]
names = prices.values[0:1].flatten()
prices.columns = names
prices = prices[1:]

main = pd.merge(simplified_main, prices, left_on="HCPCS",
                right_on="HCPCS Code", how="inner")
main.drop_duplicates(subset=["NDC"], inplace=True)
main.to_csv("fulltable")
# this tells you generic name along with company
# using this can assign a metric to generic specific to company to create new payment limit
