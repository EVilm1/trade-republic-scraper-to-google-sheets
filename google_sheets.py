import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime

import pandas as pd

def get_google_sheet(sheet_name, worksheet_name="TR"):
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]

    creds = Credentials.from_service_account_file(
        "credentials.json", scopes=scopes
    )
    client = gspread.authorize(creds)

    spreadsheet = client.open(sheet_name)

    try:
        return spreadsheet.worksheet(worksheet_name)

    except gspread.exceptions.WorksheetNotFound:
        print(f"⚠️ Worksheet '{worksheet_name}' not found → creating now")
        return spreadsheet.add_worksheet(
            title=worksheet_name,
            rows=100,
            cols=20
        )

# ----------------------------------- SETUP SHEET -----------------------------------
def setup_sheet_layout(sheet):

    cell_value = sheet.acell("B4").value

    if cell_value == "ID":
        return
    
    requests = []
    
    requests.append({
        "updateDimensionProperties": {
            "range": {
                "sheetId": sheet.id,
                "dimension": "ROWS",
                "startIndex": 1,
                "endIndex": 2
            },
            "properties": {
                "pixelSize": 40
            },
            "fields": "pixelSize"
        }
    })
    requests.append({
        "repeatCell": {
            "range": {
                "sheetId": sheet.id,
                "startRowIndex": 1,
                "endRowIndex": 2,
                "startColumnIndex": 1,
                "endColumnIndex": 8
            },
            "cell": {
                "userEnteredFormat": {
                    "backgroundColor": {"red": 0, "green": 0, "blue": 0}
                }
            },
            "fields": "userEnteredFormat.backgroundColor"
        }
    })
    requests.append({
        "repeatCell": {
            "range": {
                "sheetId": sheet.id,
                "startRowIndex": 1,
                "endRowIndex": 2,
                "startColumnIndex": 1,
                "endColumnIndex": 2
            },
            "cell": {
                "userEnteredFormat": {
                    "horizontalAlignment": "CENTER",
                    "verticalAlignment": "MIDDLE"
                }
            },
            "fields": "userEnteredFormat(horizontalAlignment,verticalAlignment)"
        }
    })
    # Logo
    sheet.update(
        range_name="B2",
        values=[[f'=IMAGE("https://raw.githubusercontent.com/EVilm1/trade-republic-scraper-to-google-sheets/refs/heads/main/icon/logo_alpha.png")']],
        value_input_option="USER_ENTERED"
    )
    # Style E2
    requests.append({
        "repeatCell": {
            "range": {
                "sheetId": sheet.id,
                "startRowIndex": 1,
                "endRowIndex": 2,
                "startColumnIndex": 4,
                "endColumnIndex": 5
            },
            "cell": {
                "userEnteredFormat": {
                    "horizontalAlignment": "RIGHT",
                    "verticalAlignment": "MIDDLE",
                    "textFormat": {
                        "fontFamily": "Lexend",
                        "fontSize": 14,
                        "bold": True,
                        "foregroundColor": {"red": 1, "green": 1, "blue": 1}
                    }
                }
            },
            "fields": "userEnteredFormat(textFormat,horizontalAlignment,verticalAlignment)"
        }
    })
    # Style F2
    requests.append({
        "repeatCell": {
            "range": {
                "sheetId": sheet.id,
                "startRowIndex": 1,
                "endRowIndex": 2,
                "startColumnIndex": 5,
                "endColumnIndex": 6
            },
            "cell": {
                "userEnteredFormat": {
                    "horizontalAlignment": "LEFT",
                    "verticalAlignment": "MIDDLE",
                    "textFormat": {
                        "fontFamily": "Lexend",
                        "fontSize": 14,
                        "bold": True,
                        "foregroundColor": {"red": 1, "green": 1, "blue": 1}
                    }
                }
            },
            "fields": "userEnteredFormat(textFormat,horizontalAlignment,verticalAlignment,numberFormat)"
        }
    })

    # ---------------- HEADERS ----------------

    headers = [
        ["", "ID", "DATE", "", "TITLE", "DESCRIPTION", "AMOUNT", "BALANCE"]
    ]

    sheet.update(range_name="A4:H4", values=headers)

    # ---------------- FORMAT HEADER ----------------

    header_format = {
        "textFormat": {
            "fontFamily": "Lexend",
            "fontSize": 10,
            "bold": True,
            "foregroundColor": {"red": 0, "green": 0, "blue": 0}
        },
        "verticalAlignment": "MIDDLE"
    }

    # B, C, G, H → center
    for col in [1, 2, 6, 7]:
        requests.append({
            "repeatCell": {
                "range": {
                    "sheetId": sheet.id,
                    "startRowIndex": 3,
                    "endRowIndex": 4,
                    "startColumnIndex": col,
                    "endColumnIndex": col+1
                },
                "cell": {
                    "userEnteredFormat": {
                        **header_format,
                        "horizontalAlignment": "CENTER"
                    }
                },
                "fields": "userEnteredFormat(textFormat,horizontalAlignment,verticalAlignment)"
            }
        })

    # E, F → align left
    for col in [4, 5]:
        requests.append({
            "repeatCell": {
                "range": {
                    "sheetId": sheet.id,
                    "startRowIndex": 3,
                    "endRowIndex": 4,
                    "startColumnIndex": col,
                    "endColumnIndex": col+1
                },
                "cell": {
                    "userEnteredFormat": {
                        **header_format,
                        "horizontalAlignment": "LEFT"
                    }
                },
                "fields": "userEnteredFormat(textFormat,horizontalAlignment,verticalAlignment)"
            }
        })
    
    # C, G, H → col align center
    for col in [2, 6, 7]:
        requests.append({
            "repeatCell": {
                "range": {
                    "sheetId": sheet.id,
                    "startRowIndex": 4,
                    "endRowIndex": 1000,
                    "startColumnIndex": col,
                    "endColumnIndex": col+1
                },
                "cell": {
                    "userEnteredFormat": {
                        "horizontalAlignment": "CENTER"
                    }
                },
                "fields": "userEnteredFormat.horizontalAlignment"
            }
        })

    # ---------------- COL ----------------

    column_sizes = [40, 90, 90, 25, 290, 160, 85, 85]  # A → H

    for i, size in enumerate(column_sizes):
        requests.append({
            "updateDimensionProperties": {
                "range": {
                    "sheetId": sheet.id,
                    "dimension": "COLUMNS",
                    "startIndex": i,
                    "endIndex": i+1
                },
                "properties": {
                    "pixelSize": size
                },
                "fields": "pixelSize"
            }
        })

    # ---------------- BORDER EXT (B4:H6) ----------------

    requests.append({
        "updateBorders": {
            "range": {
                "sheetId": sheet.id,
                "startRowIndex": 3,
                "endRowIndex": 6,
                "startColumnIndex": 1,
                "endColumnIndex": 8
            },
            "top": {"style": "SOLID_THICK", "width": 3, "color": {"red": 0, "green": 0, "blue": 0}},
            "bottom": {"style": "SOLID_THICK", "width": 3, "color": {"red": 0, "green": 0, "blue": 0}},
            "left": {"style": "SOLID_THICK", "width": 3, "color": {"red": 0, "green": 0, "blue": 0}},
            "right": {"style": "SOLID_THICK", "width": 3, "color": {"red": 0, "green": 0, "blue": 0}}
        }
    })

    # ---------------- BORDER BOTTOM HEADER (B4:H4) ----------------

    requests.append({
        "updateBorders": {
            "range": {
                "sheetId": sheet.id,
                "startRowIndex": 3,
                "endRowIndex": 4,
                "startColumnIndex": 1,
                "endColumnIndex": 8
            },
            "bottom": {"style": "SOLID_THICK", "width": 2, "color": {"red": 0, "green": 0, "blue": 0}}
        }
    })

    # ---------------- EXECUTION ----------------

    sheet.spreadsheet.batch_update({"requests": requests})

    print("✅ Layout initialized")


def push_to_google_sheets(df, sheet, mode="TR"):

    ids_column = sheet.col_values(2)
    rows_to_delete = []

    for i in range(4, len(ids_column)):
        if ids_column[i].strip() == "":
            rows_to_delete.append(i + 1)
        else:
            break

    if rows_to_delete:
        sheet.delete_rows(rows_to_delete[0], rows_to_delete[-1])

    REQUIRED_COLUMNS = [
        "id",
        "timestamp",
        "title",
        "subtitle",
        "amount.value",
        "icon",
    ]

    df = df[[c for c in REQUIRED_COLUMNS if c in df.columns]]
    df = df.fillna("")
    subtitle_clean = df["subtitle"].str.strip().str.lower()

    mode_config = {
        "TR": {
            "filter": lambda s: ~s.isin(["refusée", "pea", "saveback"]),
            "abs": False
        },
        "PEA": {
            "filter": lambda s: s == "pea",
            "abs": True
        },
        "CTO": {
            "filter": lambda s: s.isin(["saveback", "cto"]),
            "abs": True
        }
    }

    config = mode_config.get(mode)

    if config:
        df = df[config["filter"](subtitle_clean)].copy()

    if df.empty:
        print("ℹ️ There are no valid transactions to add")
        return

    existing_ids = sheet.col_values(2)
    last_known_id = str(existing_ids[4]).strip() if len(existing_ids) >= 5 else None

    if not last_known_id:
        new_rows = df.copy()
    else:
        if last_known_id in df["id"].astype(str).values:
            index = df[df["id"].astype(str) == last_known_id].index[0]
            new_rows = df.loc[:index-1]
        else:
            new_rows = df
    
    empty_messages = {
        "TR": "ℹ️ There are no new transactions to add",
        "PEA": "ℹ️ There are no new operations in the PEA to add",
        "CTO": "ℹ️ There are no new operations in the CTO to add"
    }

    if new_rows.empty:
        print("\r\033[K" + empty_messages.get(mode, "ℹ️ Nothing to add"))
        return

    new_rows = new_rows.copy()

    new_rows["amount.value"] = pd.to_numeric(
        new_rows["amount.value"].astype(str).str.replace(",", ".", regex=False),
        errors="coerce"
    )

    if config and config["abs"]:
        new_rows["amount.value"] = new_rows["amount.value"].abs()
    
    values_to_insert = new_rows[[
        "id",
        "timestamp",
        "title",
        "subtitle",
        "amount.value"
    ]].astype(object).values.tolist()

    values_to_insert = [["", row[0], row[1], "", row[2], row[3], row[4]] for row in values_to_insert]

    # Col | Content
    # ----|--------
    # A	  | empty
    # B	  | id
    # C	  | timestamp
    # D	  | title
    # E	  | subtitle
    # F	  | amount
    # G	  | solde
    # H	  | icon

    sheet.insert_rows(values_to_insert, row=5)
    sheet.format("D:D", {"horizontalAlignment": "CENTER"})

    # ---------------- BALANCE ----------------

    formulas = []

    for i in range(len(values_to_insert)):

        sheet_row = i + 5
        formula = f"=G{sheet_row}+H{sheet_row+1}"

        formulas.append([formula])

    # 🔹 Mise à jour d’un bloc de cellules en une seule requête
    sheet.update(
        range_name=f"H5:H{5+len(formulas)-1}",
        values=formulas,
        value_input_option="USER_ENTERED"
    )

    # ---------------- FORMAT ----------------

    start_row = 5
    end_row = 5 + len(values_to_insert) - 1 

    # -------- GLOBAL FORMAT --------

    requests = [{
        "repeatCell": {
            "range": {
                "sheetId": sheet.id,
                "startRowIndex": start_row-1,
                "endRowIndex": end_row,
                "startColumnIndex": 1,
                "endColumnIndex": 8
            },
            "cell": {
                "userEnteredFormat": {
                    "textFormat": {
                        "fontFamily": "Lexend",
                        "fontSize": 10,
                        "foregroundColor": {"red": 0, "green": 0, "blue": 0}
                    }
                }
            },
            "fields": "userEnteredFormat.textFormat"
        }
    }]

    # -------- ID GREY --------

    requests.append({
        "repeatCell": {
            "range": {
                "sheetId": sheet.id,
                "startRowIndex": start_row-1,
                "endRowIndex": end_row,
                "startColumnIndex": 1,
                "endColumnIndex": 2
            },
            "cell": {
                "userEnteredFormat": {
                    "textFormat": {
                        "fontFamily": "Lexend",
                        "fontSize": 10,
                        "foregroundColor": {"red": 0.6, "green": 0.6, "blue": 0.6}
                    }
                }
            },
            "fields": "userEnteredFormat.textFormat"
        }
    })

    # -------- EXCEPTIONS --------

    light_blue = {"red": 0.85, "green": 0.92, "blue": 1.0}
    light_green = {"red": 0.85, "green": 0.95, "blue": 0.85}

    for i in range(len(values_to_insert)):

        sheet_row = i + 5

        title_value = values_to_insert[i][4].strip().lower()
        subtitle_value = values_to_insert[i][5].strip().lower()

        amount_value = values_to_insert[i][6]

        try:
            amount_float = float(amount_value)
        except:
            amount_float = None

        background = None

        if subtitle_value in ["ordre d'achat", "plan d'épargne exécuté"]:
            background = light_blue

        if title_value == "intérêts":
            background = light_green

        if background:
            requests.append({
                "repeatCell": {
                    "range": {
                        "sheetId": sheet.id,
                        "startRowIndex": sheet_row-1,
                        "endRowIndex": sheet_row,
                        "startColumnIndex": 1,
                        "endColumnIndex": 8
                    },
                    "cell": {
                        "userEnteredFormat": {
                            "backgroundColor": background
                        }
                    },
                    "fields": "userEnteredFormat.backgroundColor"
                }
            })

        if amount_float is not None and amount_float != 0:

            amount_color = {"red": 0, "green": 0.6, "blue": 0} if amount_float > 0 else {"red": 0.8, "green": 0, "blue": 0}

            requests.append({
                "repeatCell": {
                    "range": {
                        "sheetId": sheet.id,
                        "startRowIndex": sheet_row-1,
                        "endRowIndex": sheet_row,
                        "startColumnIndex": 6,
                        "endColumnIndex": 7
                    },
                    "cell": {
                        "userEnteredFormat": {
                            "numberFormat": {
                                "type": "CURRENCY",
                                "pattern": "#,##0.00 €"
                            },
                            "textFormat": {
                                "fontFamily": "Lexend",
                                "fontSize": 10,
                                "foregroundColor": amount_color
                            }
                        }
                    },
                    "fields": "userEnteredFormat(numberFormat,textFormat)"
                }
            })

    sheet.spreadsheet.batch_update({"requests": requests})

    # ---------------- ADD ICONS COL D ----------------

    icon_values = []

    for i in range(len(new_rows)):
        icon = str(new_rows.iloc[i]["icon"]).strip()

        if icon:
            url = f"https://assets.traderepublic.com/img/{icon}/light.min.svg"
            icon_values.append([f'=IMAGE("{url}")'])
        else:
            icon_values.append([""])

    if icon_values:
        sheet.update(
            range_name=f"D5:D{5+len(icon_values)-1}",
            values=icon_values,
            value_input_option="USER_ENTERED"
        )

    # ---------------- HEADER ----------------

    today_str = datetime.now().strftime("%d/%m/%Y")

    raw_value = sheet.acell("H5", value_render_option="UNFORMATTED_VALUE").value

    header_labels = {
        "TR": "BALANCE AS OF",
        "PEA": "TOTAL DEPOSITS AS OF",
        "CTO": "TOTAL DEPOSITS AS OF"
    }

    label = header_labels.get(mode, "VALUE")

    sheet.update("E2", [[f"{label} {today_str} :"]])
    sheet.update("F2", [[raw_value]])

    sheet.format("F2", {
        "numberFormat": {
            "type": "CURRENCY",
            "pattern": "#,##0.00 €"
        }
    })

    n = len(values_to_insert)
    print(f"\r\033[K✅ {n} new operation{'s' if n != 1 else ''} added to the worksheet {sheet.title} in the sheet {sheet.spreadsheet.title}")