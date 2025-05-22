# from helper import g_auth_client


from functions.gfunc import get_sheet, get_folder
from constants import SHEET_KEY, FOLDER_KEY, DOWNLOAD_PATH
import pandas as pd




if __name__ == "__main__":

    # sheet = get_sheet(sheet_key=SHEET_KEY, sheet_name=None)
    # df = pd.DataFrame(sheet)
    # print(df.head(2))

    data = get_folder(folder_key = FOLDER_KEY , download_path= DOWNLOAD_PATH)
    

    # sheet = client.open("Iamhaut_RnD_Results")


# 1X4LJMxPokd0wmU1AojmrlhmVpWRV7Ywh