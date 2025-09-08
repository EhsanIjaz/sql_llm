# from helper import g_auth_client


from src.connector_aws_gdrive.gdrive_funcs import get_sheet, get_latest_file
from src.constants import *
import pandas as pd




if __name__ == "__main__":

    # sheet = get_sheet(sheet_key=SHEET_KEY, sheet_name=None)
    # df = pd.DataFrame(sheet)
    # print(df.head(2))

    data = get_latest_file(folder_key = FOLDER_KEY , download_path= DOWNLOADS_PATH)
    

    # sheet = client.open("Iamhaut_RnD_Results")


# 1X4LJMxPokd0wmU1AojmrlhmVpWRV7Ywh
# from helper import g_auth_client

from src.connector_aws_gdrive.gdrive_funcs import get_sheet, get_latest_file
from src.constants import SHEET_KEY, FOLDER_KEY, DOWNLOADS_PATH
import pandas as pd



from src.connector_aws_gdrive.gdrive_funcs import get_sheet, get_folder 
from src.constants import SHEET_KEY, FOLDER_KEY, DOWNLOADS_PATH
import pandas as pd
# from functions.dataloader import clean_and_rename_file, latest_file, get_latest_file
from src.constants.data_paths import *



if __name__ == "__main__":

    # sheet = get_sheet(sheet_key=SHEET_KEY, sheet_name=None)
    # df = pd.DataFrame(sheet)
    # print(df.head(2))


    data = get_folder(folder_key = FOLDER_KEY , download_path= DOWNLOADS_PATH)

    # get the data 
    # data = get_latest_file(folder_key = FOLDER_KEY , download_path= DOWNLOADS_PATH)
    
    # #clean the folder and load
    # file = clean_and_rename_file(DOWNLOADS_PATH)
   
   
    print("the download path",DOWNLOADS_PATH)
    a = get_latest_file(DOWNLOADS_PATH)
    # b = latest_file(DOWNLOADS_PATH)
    print(a)
    # print(b)
    # print(SCRIPT_DIR)
    # latest_file_1 = latest_file(DOWNLOADS_PATH)


    # sheet = client.open("Iamhaut_RnD_Results")


# 1X4LJMxPokd0wmU1AojmrlhmVpWRV7Ywh