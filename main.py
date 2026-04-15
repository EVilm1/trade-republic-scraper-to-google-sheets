import sys
import os
import json
import asyncio
import configparser
import websockets
import time
import getpass
import pandas as pd

import requests
import base64
import uuid
import hashlib

from selenium import webdriver
from selenium.webdriver.chrome.options import Options


from google_sheets import (
    setup_sheet_layout,
    push_to_google_sheets,
    get_google_sheet
)

def save_phone_number(config, phone_number):
    if not config.has_section("secret"):
        config.add_section("secret")

    config.set("secret", "phone_number", phone_number)

    with open("config.ini", "w") as configfile:
        config.write(configfile)


# ----------------------------------- TR -----------------------------------

def flatten_and_clean_json(all_data, sep="."):
    all_keys = []  # Used to preserve the column order
    flattened_data = []

    def flatten(nested_json, parent_key=""):
        """Recursively flattens a nested JSON."""
        flat_dict = {}
        for key, value in nested_json.items():
            new_key = f"{parent_key}{sep}{key}" if parent_key else key
            if isinstance(value, dict):
                flat_dict.update(flatten(value, new_key))
            else:
                flat_dict[new_key] = value

            if new_key not in all_keys:
                all_keys.append(new_key)

        return flat_dict

    # Flatten all entries and collect all possible columns
    for item in all_data:
        flat_item = flatten(item)
        flattened_data.append(flat_item)

    # Ensure each dictionary has all columns, keeping the order unchanged
    complete_data = [
        {key: item.get(key, None) for key in all_keys} for item in flattened_data
    ]

    return complete_data


def transform_data_types(df):
    timestamp_columns = ["timestamp"]  # Timestamp type columns
    for col in timestamp_columns:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce").dt.strftime("%d/%m/%Y")

    amount_columns = [
        "amount.value",
        "amount.fractionDigits",
        "subAmount.value",
        "subAmount.fractionDigits",
    ]
    for col in amount_columns:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
            df[col] = df[col].apply(
                lambda x: str(x).replace(".", ",") if pd.notna(x) else x
            )

    return df


async def connect_to_websocket():
    """
    Asynchronous function to establish a WebSocket connection to the TradeRepublic API.
    :return: The WebSocket object connected to the TradeRepublic API.
    """
    websocket = await websockets.connect("wss://api.traderepublic.com")
    locale_config = {
        "locale": "fr",
        "platformId": "webtrading",
        "platformVersion": "safari - 18.3.0",
        "clientId": "app.traderepublic.com",
        "clientVersion": "3.151.3",
    }
    await websocket.send(f"connect 31 {json.dumps(locale_config)}")
    await websocket.recv()  # Connection response

    return websocket


async def fetch_transaction_details(websocket, transaction_id, token, message_id):
    payload = {"type": "timelineDetailV2", "id": transaction_id, "token": token}
    message_id += 1
    await websocket.send(f"sub {message_id} {json.dumps(payload)}")
    response = await websocket.recv()
    await websocket.send(f"unsub {message_id}")
    await websocket.recv()

    start_index = response.find("{")
    end_index = response.rfind("}")
    response_data = json.loads(
        response[start_index : end_index + 1]
        if start_index != -1 and end_index != -1
        else "{}"
    )

    transaction_data = {}

    for section in response_data.get("sections", []):
        if section.get("title") == "Transaction":
            for item in section.get("data", []):
                header = item.get("title")
                value = item.get("detail", {}).get("text")
                if header and value:
                    transaction_data[header] = value

    return transaction_data, message_id


async def fetch_all_transactions(token, extract_details):
    all_data = []
    message_id = 0

    async with await connect_to_websocket() as websocket:
        after_cursor = None
        while True:
            payload = {"type": "timelineTransactions", "token": token}
            if after_cursor:
                payload["after"] = after_cursor

            message_id += 1
            await websocket.send(f"sub {message_id} {json.dumps(payload)}")
            response = await websocket.recv()
            await websocket.send(f"unsub {message_id}")
            await websocket.recv()
            start_index = response.find("{")
            end_index = response.rfind("}")
            response = (
                response[start_index : end_index + 1]
                if start_index != -1 and end_index != -1
                else "{}"
            )
            data = json.loads(response)

            if not data.get("items"):
                break

            if extract_details:
                for transaction in data["items"]:
                    transaction_id = transaction.get("id")
                    if transaction_id:
                        details, message_id = await fetch_transaction_details(
                            websocket, transaction_id, token, message_id
                        )
                        transaction.update(details)
                    all_data.append(transaction)
            else:
                all_data.extend(data["items"])

            after_cursor = data.get("cursors", {}).get("after")
            if not after_cursor:
                break


    flattened_data = flatten_and_clean_json(all_data)

    if flattened_data:
        df = pd.DataFrame(flattened_data)
        df = df.dropna(axis=1, how="all")
        df = transform_data_types(df)

        # ---------------- GOOGLE SHEETS ----------------

        print(f"\r🔄​ Updating transactions...", end="", flush=True)
        sheet_tr = get_google_sheet(sheet_name, worksheet_name=worksheet_tr_name)
        setup_sheet_layout(sheet_tr)
        push_to_google_sheets(df, sheet_tr, mode="TR")

        print(f"\r🔄​ Updating PEA...", end="", flush=True)
        sheet_pea = get_google_sheet(sheet_name, worksheet_name=worksheet_pea_name)
        setup_sheet_layout(sheet_pea)
        push_to_google_sheets(df, sheet_pea, mode="PEA")

        print(f"\r🔄​ Updating CTO...", end="", flush=True)
        sheet_cto = get_google_sheet(sheet_name, worksheet_name=worksheet_cto_name)
        setup_sheet_layout(sheet_cto)
        push_to_google_sheets(df, sheet_cto, mode="CTO")

        # ---------------- EXPORT ----------------

        if output_format.lower() == "json":
            output_path = os.path.join(output_folder, "trade_republic_transactions.json")
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(all_data, f, indent=4, ensure_ascii=False)
            print("💾 Transactions saved in JSON file")

        else:
            output_path = os.path.join(output_folder, "trade_republic_transactions.csv")
            df.to_csv(output_path, index=False, sep=";", encoding="utf-8-sig")
            print("💾 Transactions saved in CSV file")
            

def generate_device_info():
    device_id = hashlib.sha512(uuid.uuid4().bytes).hexdigest()
    device_info = {
        "stableDeviceId": device_id
    }
    return base64.b64encode(
        json.dumps(device_info).encode("utf-8")
    ).decode("utf-8")


def get_waf_token():
    """
    Robustly retrieves the AWS WAF token via Selenium.
    - Tries first via cookies
    - Then fallback via window.AWSWafIntegration.getToken()
    """

    print("\033[1A\r\033[K🤖 Getting TR token...")

    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1280,900")

    driver = None

    try:
        driver = webdriver.Chrome(options=options)

        # Hide Selenium 
        driver.execute_cdp_cmd(
            "Page.addScriptToEvaluateOnNewDocument",
            {
                "source": """
                    Object.defineProperty(navigator, 'webdriver', {
                        get: () => undefined
                    });

                    Object.defineProperty(navigator, 'languages', {
                        get: () => ['fr-FR', 'fr']
                    });

                    Object.defineProperty(navigator, 'platform', {
                        get: () => 'MacIntel'
                    });
                """
            }
        )

        driver.get("https://app.traderepublic.com/")

        # Allow time for the WAF to initialize
        time.sleep(5)

        waf_token = None

        # Main method: cookies
        for cookie in driver.get_cookies():
            if "aws-waf-token" in cookie.get("name", ""):
                waf_token = cookie["value"]
                break

        # Fallback: JS retrieval if the cookie does not appear
        if not waf_token:
            try:
                waf_token = driver.execute_script("""
                    return (
                        window.AWSWafIntegration &&
                        typeof window.AWSWafIntegration.getToken === 'function'
                    )
                        ? window.AWSWafIntegration.getToken()
                        : null;
                """)
            except Exception:
                pass

        if not waf_token:
            raise Exception("Unable to retrieve the AWS WAF token")

        print("\033[1A\r\033[K✅ Token found")
        return waf_token

    finally:
        if driver:
            driver.quit()


def exit_error(message):
    print(f"\n❌ {message}")
    sys.exit(1)


def get_tr_session_api(phone_number, pin):
    """
    Robust Trade Republic API Login:
    - WAF token retrieval
    - Device info generation
    - Login
    - Handling of possible SMS resend
    - Clean retrieval of the tr_session cookie
    """
    waf_token = get_waf_token()
    device_info = generate_device_info()

    headers = {
        "Accept": "*/*",
        "Accept-Language": "fr-FR,fr;q=0.9,en;q=0.8",
        "Cache-Control": "no-cache",
        "Pragma": "no-cache",
        "Content-Type": "application/json",
        "Origin": "https://app.traderepublic.com",
        "Referer": "https://app.traderepublic.com/",
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/125.0.0.0 Safari/537.36"
        ),
        "x-aws-waf-token": waf_token,
        "x-tr-app-version": "13.40.5",
        "x-tr-device-info": device_info,
        "x-tr-platform": "web"
    }

    login_response = requests.post(
        "https://api.traderepublic.com/api/v1/auth/web/login",
        json={
            "phoneNumber": phone_number,
            "pin": pin
        },
        headers=headers,
        timeout=20
    )

    if login_response.status_code == 401:
        exit_error("Incorrect PIN")

    if login_response.status_code != 200:
        raise Exception(
            f"❌ Login API failed ({login_response.status_code})\n"
            f"{login_response.text}"
        )

    try:
        login_data = login_response.json()
    except Exception:
        raise Exception("❌ Invalid response")

    process_id = login_data.get("processId")
    countdown = login_data.get("countdownInSeconds")

    if not process_id:
        raise Exception(
            "❌ Missing processId: Incorrect PIN or modified Trade Republic"
        )

    print(f"\r📲 Enter the 2FA code ({countdown}s remaining or type 'SMS' to resend) : ", end="", flush=True)
    code = input()

    # SMS resend handling
    if code.upper() == "SMS":
        resend_response = requests.post(
            f"https://api.traderepublic.com/api/v1/auth/web/login/{process_id}/resend",
            headers=headers,
            timeout=20
        )

        if resend_response.status_code != 200:
            raise Exception(
                f"❌ Unable to resend SMS ({resend_response.status_code})"
            )

        code = input("📲 New code received : ").strip()

    verify_response = requests.post(
        f"https://api.traderepublic.com/api/v1/auth/web/login/{process_id}/{code}",
        headers=headers,
        timeout=20
    )

    if verify_response.status_code != 200:
        exit_error("Incorrect 2FA code")

    # extraction of the tr_session cookie
    tr_session = None

    for cookie in verify_response.cookies:
        if cookie.name == "tr_session":
            tr_session = cookie.value
            break

    # Fallback if requests.cookies finds nothing
    if not tr_session:
        set_cookie = verify_response.headers.get("Set-Cookie", "")

        for part in set_cookie.split(","):
            if "tr_session=" in part:
                try:
                    tr_session = (
                        part.split("tr_session=")[1]
                        .split(";")[0]
                        .strip()
                    )
                    break
                except Exception:
                    pass

    if not tr_session:
        raise Exception("❌ tr_session cookie not found")

    print("\033[1A\r\033[K✅ Logged in")
    return tr_session


if __name__ == "__main__":
    # Load configuration
    config = configparser.ConfigParser()
    config.read("config.ini")
    sheet_name = config.get("google_sheets", "sheet_name")
    worksheet_tr_name = config.get("google_sheets", "worksheet_tr_name")
    worksheet_pea_name = config.get("google_sheets", "worksheet_pea_name")
    worksheet_cto_name = config.get("google_sheets", "worksheet_cto_name")

    # ---------------- PHONE NUMBER ----------------
    if config.has_option("secret", "phone_number"):
        phone_number = config.get("secret", "phone_number").strip()
    else:
        phone_number = ""

    if not phone_number:
        phone_number = input("📞 Enter your Trade Republic phone number (in the format +33712345678) : ").strip()
        save_phone_number(config, phone_number)

    # ---------------- PIN ----------------
    pin = getpass.getpass("⚡ Enter your Trade Republic PIN : ")
    
    output_format = config.get(
        "general", "output_format"
    )  # Output format: json or csv
    output_folder = config.get("general", "output_folder")
    extract_details = config.getboolean("general", "extract_details", fallback=False)
    os.makedirs(output_folder, exist_ok=True)

    # Validate output format
    if output_format.lower() not in ["json", "csv"]:
        print(
            f"❌ Unknown format '{output_format}'. Please enter 'json' or 'csv'."
        )
        sys.exit(1)

    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
    }

    session_token = get_tr_session_api(phone_number, pin)

    if not session_token:
        print("❌ Unable to retrieve token")
        sys.exit(1)

    # Execute
    asyncio.run(fetch_all_transactions(session_token, extract_details))
    print("\r")