# sql_llm

## 🔐 Google Drive API Authentication Setup

To enable access to Google Drive and Google Sheets, follow these steps to create and place your credentials file:

### Step 1: Create a Service Account and Download JSON Key

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Select your project (or create a new one).
3. Navigate to **IAM & Admin > Service Accounts**
4. Click **Create Service Account**
   - Provide a name like `gdrive-access-bot`
   - Assign basic role: `Editor` or `Viewer` (as needed)
5. After creating, go to the Service Account → **Manage Keys**
6. Click **Add Key > Create New Key > JSON**
7. This will download a file like: `gdrive_creds.json`

---

### Step 2: Where to Place the File

1. Create a `conf/` folder in your project root if it doesn't exist
2. Move the downloaded `gdrive_creds.json` file into it
