import pandas as pd

def add_goodcode_from_excel():
    url = "Copy of EDUKA__CODE__BANK__2023_my.xlsx"
    df = pd.read_excel(url, engine='openpyxl', sheet_name=None)

    print(df.keys())
    print(df['ZA_2023'].keys())

def update_user_code():
    pass

