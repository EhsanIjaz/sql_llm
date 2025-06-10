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
# from helper import g_auth_client

from functions.gfunc import get_sheet, get_folder
from constants import SHEET_KEY, FOLDER_KEY, DOWNLOAD_PATH
import pandas as pd



from functions.gfunc import get_sheet, get_files 
from constants import SHEET_KEY, FOLDER_KEY, DOWNLOAD_PATH
import pandas as pd
from functions.dataloader import clean_and_rename_file, latest_file, get_files
from constants.data_costant import *



if __name__ == "__main__":

    # sheet = get_sheet(sheet_key=SHEET_KEY, sheet_name=None)
    # df = pd.DataFrame(sheet)
    # print(df.head(2))


    data = get_folder(folder_key = FOLDER_KEY , download_path= DOWNLOAD_PATH)

    # get the data 
    # data = get_files(folder_key = FOLDER_KEY , download_path= DOWNLOAD_PATH)
    
    # #clean the folder and load
    # file = clean_and_rename_file(DOWNLOAD_PATH)
   
   
    print("the download path",DOWNLOAD_DIR)
    a = get_files(DOWNLOAD_DIR)
    b = latest_file(DOWNLOAD_DIR)
    print(a)
    print(b)
    # print(SCRIPT_DIR)
    # latest_file_1 = latest_file(DOWNLOAD_PATH)


    # sheet = client.open("Iamhaut_RnD_Results")


# 1X4LJMxPokd0wmU1AojmrlhmVpWRV7Ywh