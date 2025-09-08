# sql_llm

## 🔐 Google Drive API Authentication Setup

To enable access to Google Drive and Google Sheets, follow these steps to create and place your credentials file:

### Step 1: Clone the Repository and Install Dependencies

```bash
git clone https://github.com/EhsanIjaz/sql_llm.git
cd sql_llm
```

### Step 2: Activate Environment

```bash
pixi shell
```
Or 
```bash
pixi install
```
## Data Loading Process

### Google Drive

### Step 1: Create a Service Account and Download JSON Key

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Select your project (or create a new one).
3. Navigate to **IAM & Admin > Service Accounts**
4. Click **Create Service Account** and give it a descriptive name (e.g., `gdrive-access-bot`).
   - Assign basic role: `Editor` or `Viewer` (as needed)
5. After creating, go to the Service Account → **Manage Keys**
6. Click **Add Key > Create New Key > JSON**
7. This will download a file like: `gdrive_creds.json`

---
### Step 2: Where to Place the File

1. Paste teh json file into `config/` folder in your project root.
2. Open the file `src/constants/app_constant.py`.
3. Replace the placeholder values for your Google Drive `Folder ID` and `Google Sheets ID` with the `FOLDER_KEY`, `SHEET_KEY` from your uploaded files.

During application running it get the data file-from g_drive and cached into the local folder

## 🔐 AWS Authentication Setup

### AWS (S3)

### Step 1: AWS cofiguarateion adding procedure.

Create the file named `config.env` add AWS confugurations 

```bash
AWS_LLM_BUCKET = r""
AWS_SERVER_PUBLIC_KEY = r""
AWS_SERVER_SECRET_KEY = r""
AWS_REGION = r""
```
Fill in the empty strings with your actual AWS configuration values.

### Step 2: AWS cofiguarateion adding procedure.

1. Open the file `src/constants/app_constant.py`.
2. upload the data into teh directory and replace it with placeholder values for your AWS `Data Directory` with the `REMOTE_DEFAULT_DATA_DIRECTORY`.

## Run the Application

This prject is using three ways use can use it with the:

1. `OpenAPIkey`
2. `OpenRouterAiAPIkey`
3. With your `Personal model` i tested it with `defog/sqlcoder-7b-2` model locally.

### Run the Streamlit App

Inside the pixi shell, run:

`streamlit run query_runner.py --server.port 8056`

This will start the app at:
👉 `http://localhost:8056`

