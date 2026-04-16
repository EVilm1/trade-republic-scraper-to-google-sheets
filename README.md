<!-- PROJECT HEADER -->
<br />
<div align="center">
  <img src="https://github.com/user-attachments/assets/229873ba-aa17-47dc-a5b5-2c572f195da9" alt="Logo TradeRepublic to Google Sheets" width="400">
  <h1 align="center">
    Export Trade Republic transactions to Google Sheets !
    
  </h1>
  <h4 align="center">
    This project allows you to export all your Trade Republic transactions to Google Sheets with automatic formatting. Transactions are organized into three separate sheets: payments, PEA, and CTO. The script runs locally and only stores your phone number. Your PIN is never saved, and you will be prompted to enter both your PIN and 2FA code each time the script runs.
  </h4>
  <span align="center">
    Here is an example of the result in Sheets (in french for other languages see <a href="#filter-transactions-paymentspeacto-by-languages-other-than-french">here</a>) :
  </span>
  <br /><br />
  <img src="https://github.com/user-attachments/assets/95d00cab-1075-439b-99f9-0a30bf4feebc" alt="example" width="680">
  <br />
  <br />
  <span>
    Inspired on <a href="https://github.com/BenjaminOddou">BenjaminOddou</a>'s 
    <a href="https://github.com/BenjaminOddou/trade_republic_scraper">trade-republic-scraper</a>,
    with modifications and improvements.
  </span>
  <br />
  <br />
  <span align="center">If you like this project and find it useful, please feel free to let me know ↓</span>
  <br />
  <br />
  <a href="https://www.buymeacoffee.com/EVilm1" target="_blank"><img src="https://www.buymeacoffee.com/assets/img/custom_images/orange_img.png" alt="Buy Me A Coffee" style="height: 41px !important;width: 174px !important;box-shadow: 0px 3px 2px 0px rgba(190, 190, 190, 0.5) !important;-webkit-box-shadow: 0px 3px 2px 0px rgba(190, 190, 190, 0.5) !important;" ></a>
</div>

---

## 1) Prerequisites

Make sure you have the following installed on your system :

- Python 3.10 or higher (Python 3.14.2 is used for this project)
- Google Chrome (required for Selenium automation)

To check if Python is installed :

```bash
python --version
pip --version
```

If Python is not installed, download it from:
https://www.python.org/downloads/

During installation on Windows, make sure to check:
✔ Add Python to PATH

## 2) Installation

Download and extract the project folder.
Then open a terminal inside the project directory.

### 2.1 Create a Virtual Environment

It is strongly recommended to use a virtual environment to isolate dependencies.

After browsing to the correct project installation directory :
```bash
python -m venv .venv
```

#### Activate it :

#### Windows (PowerShell / CMD) :
```bash
.venv\Scripts\activate
```

#### macOS / Linux:
```bash
source .venv/bin/activate
```

Once activated, you should see `(.venv)` in your terminal.

### 2.2 Update pip / Install Dependencies

Before installing dependencies, update pip :

```bash
python -m pip install --upgrade pip
```

Install all required Python packages using :

```bash
pip install -r requirements.txt
```

This project typically requires:
```bash
- pandas
- requests
- websockets
- selenium
- google-auth / gspread (for Google Sheets integration)
```

### 2.3 Selenium Setup

This project uses Selenium to retrieve authentication tokens. No manual ChromeDriver installation is required.  
After installing dependencies, Selenium will automatically download and manage the correct driver version (Selenium Manager).

> [!NOTE]
> You can install it manually if you have any issues :
> ```bash
> pip install selenium
> ```

## 3)​ Set up the configuration file (config.ini) 📄

Before running the script, it is important to configure the `config.ini` file.  
It contains:

- General settings :
  - `output_format` : json or csv.
  - `output_folder` : “out” folder by default.
  - `extract_details` : True.
    
- Google Sheets settings :
  - `sheet_name` The exact name of your spreadsheet in your Google Drive.
  - `worksheet_tr_name` : The exact name of the sheet in your spreadsheet for transactions.
  - `worksheet_pea_name` : The exact name of the sheet in your spreadsheet for your PEA.
  - `worksheet_cto_name` : The exact name of the sheet in your spreadsheet for your CTO.

> [!IMPORTANT]
> ✏️ Edit the config file to match the names of your spreadsheets and sheets inside,  (if the sheets don't exist, they will be created)

> [!NOTE]
> You can leave the phone number field blank. The first run will also ask for your Trade Republic phone number (It must not contain any spaces and must include your area code. For example, in France : `+33712345678`) After the first run, you will no longer be asked and it will be stored in the config.ini file.

## 4) Set up Google Sheets and Google Cloud 🔧

To configure the script's access to your Google account so it can access Google Sheets, go to:

https://console.cloud.google.com/

Create a new project by clicking `Select a project` in the top-left corner, then `New project` in the window that appears, You can name your project `“tr-scraper”`, for example.
Once created, select it under `Select a project`:

<kbd> <img width="500" alt="image" src="https://github.com/user-attachments/assets/78e2983a-68fc-4136-b3b7-94311d2215d5" /> </kbd>

### 4.1 Enable APIs

In the menu on the left: `APIs & Services` -> `API Library`, enable the two APIs used:

`Google Drive API` : https://console.cloud.google.com/apis/library/drive.googleapis.com  
`Google Sheets API` : https://console.cloud.google.com/apis/library/sheets.googleapis.com

### 4.2 Create a `service account`

In the menu on the left : `IAM & Admin` -> `Service accounts` (https://console.cloud.google.com/iam-admin/serviceaccounts)

Create a service account : Click `+ Create service account`; you can name it `“tr-scraper-bot”`, for example. Leave the fields under `Permissions (optional)` and `Principals with access (optional)` blank, then click `Done`. 

<kbd> <img width="1845" height="443" alt="image" src="https://github.com/user-attachments/assets/2014abbb-455a-4b5d-be06-e7d321871450" /> </kbd>

Next, copy the email address from the service account.  
In the Google Sheet where you want the results to appear, share access to the copied email address and set the permissions to `editor`:

<kbd> <img width="400" alt="image" src="https://github.com/user-attachments/assets/58625657-6555-4327-99f1-071f59973e06" /> </kbd>

### 4.3 Create the JSON access key

In the `Service accounts` tab, click the three dots in the `Actions` column on the right -> `Manage keys`

On the `Keys` page :  
Click `Add key` -> `Create new key`, then select `JSON` :

<kbd> <img width="400" alt="image" src="https://github.com/user-attachments/assets/0fc95cc9-ae5a-4543-90a3-8aaebb4e9cae" /> </kbd>
<kbd> <img width="2208" height="568" alt="image" src="https://github.com/user-attachments/assets/bd7fd1c9-db2d-4792-b994-660613a949e5" /> </kbd>

> [!IMPORTANT]
> The JSON key should have downloaded to your computer. Do not share it! Place the JSON key directly in the project root directory, renaming it `credentials.json`, next to `main.py`.

## 5) Run the script ▶️

Make sure you have completed the `config.ini` file as explained [here](#3-set-up-the-configuration-file-configini-).

Next, open your project folder from a command line interface.

### Option 1 : Run the script from PowerShell / CMD

#### On Windows (PowerShell / CMD), enable the virtual environment:
```bash
.venv\Scripts\activate
```
#### Run the script : 
```bash
python main.py
```

### Option 2 : Run the script from start.bat / Windows shortcut

A start.bat file already included in the project root directory allows you to run the script and automatically activate the virtual environment:
```bat
@echo off
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
    echo ❌ python.exe not found
    pause
    exit /b
)
.venv\Scripts\python.exe main.py
pause
```

> [!TIP]
> You can create a Windows shortcut for `start.bat` and change its icon (see folder [icon/logo_light.ico](/icon/logo_light.ico)) to get this kind of result:
> 
> <kbd> <img width="148" height="120" alt="image" src="https://github.com/user-attachments/assets/ef5d25ce-c5f8-4bd0-999e-734c044f8a49" /> </kbd>

### When the script is running 

> [!IMPORTANT]
> A message will appear the first time you use it because the Script tries to load logos from the internet. Accept the warning and see if it works. If it doesn't work, just delete the sheet from the spreadsheet and run the Script again (the sheet will be recreated).
> <kbd> <img width="1871" height="72" alt="image" src="https://github.com/user-attachments/assets/63e72320-15cb-4c0b-9178-c791cdc36c20" /> </kbd>

#### The script will :

1. Open a headless browser (Selenium)
2. Retrieve authentication token
3. Connect to Trade Republic API via WebSocket
4. Fetch all transactions
5. Update Google Sheets (with aesthetic formatting on first run, and if the file specified in `config.ini` does not exist, it creates it)
6. Export data : JSON OR CSV

## 6) Troubleshooting and improvements

### Filter transactions (Payments/PEA/CTO) by languages other than French
This project is designed to work with a French TradeRepublic account that returns descriptions in French (which allows you to filter transactions between payments, the PEA, and the CTO).
I haven't been able to test it in other languages because I don't know what their descriptions look like. If you'd like me to add a specific language, please let me know and I'll work on

### Sort transactions in other sheets 
Would you like to sort data in another sheet, such as crypto transactions, for example? I don't use it myself, but if you're interested, let me know and I'll add it. 

### Selenium issues
- Make sure Chrome is installed
- Update Chrome if driver fails

### WebSocket connection errors
- Check internet connection
- Retry login (Trade Republic may rate-limit requests)

### Google Sheets errors
- Ensure credentials / API access is correctly configured

## 7) Security Notes

- Your PIN is never stored.
- The login process always asks for your 2FA code, just like when you log in online.
- Phone number is saved locally in `config.ini`.
- Authentication uses Trade Republic official web endpoints.
