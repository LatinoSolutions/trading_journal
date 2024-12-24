import streamlit as st
from datetime import datetime, date
import matplotlib.pyplot as plt
import gspread
from google.oauth2.service_account import Credentials

# -----------------------
# INTEGRACIÓN GOOGLE SHEETS
# -----------------------
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

# Construir las credenciales desde Streamlit Secrets
credentials_info = {
    "type": st.secrets["type"],
    "project_id": st.secrets["project_id"],
    "private_key_id": st.secrets["private_key_id"],
    "private_key": st.secrets["private_key"],
    "client_email": st.secrets["client_email"],
    "client_id": st.secrets["client_id"],
    "auth_uri": st.secrets["auth_uri"],
    "token_uri": st.secrets["token_uri"],
    "auth_provider_x509_cert_url": st.secrets["auth_provider_x509_cert_url"],
    "client_x509_cert_url": st.secrets["client_x509_cert_url"],
}

# Crear credenciales usando los datos cargados desde Secrets
credentials = Credentials.from_service_account_info(credentials_info, scopes=SCOPES)

# Autorizar el cliente de Google Sheets
gc = gspread.authorize(credentials)

###############################################################################
#                   MAPEO DE COLUMNAS Y ORDEN EXPLÍCITO
###############################################################################
CSV_HEADERS_MAP = {
    "trade_number":         "Trade #",
    "datetime_final":       "Datetime Final",
    "pair":                 "Pair",
    "type":                 "Type",
    "timing":               "Timing",
    "screenshot_url":       "Screenshot URL",
    "result":               "Result",
    "pnl_usd":              "PnL (USD)",
    "new_equity":           "Equity final",
    "comments":             "Comments",
    "delta_percent":        "Delta % vs 10k",
    "daily_goal_percent":   "Daily Goal (%)",
    "daily_goal_value":     "Daily Goal Value",
    "selected_confluences": "Confluences",
    "confluences_count":    "Confluences #",
    "approach1_data":       "Approach #1 Info",
    "approach2_data":       "Approach #2 Info",
    "approach3_data":       "Approach #3 Info",
    "approach4_data":       "Approach #4 Info",
    "timestamp_saved":      "Timestamp Saved"
}

FIELDNAMES_ORDER = list(CSV_HEADERS_MAP.keys())

###############################################################################
#                     FUNCIONES PARA GOOGLE SHEETS
###############################################################################
def get_trade_count():
    """Cuenta el número de trades en Google Sheets."""
    sh = gc.open("Trades Journal")  # Cambia por el nombre de tu Google Sheet
    worksheet = sh.worksheet("Journal2024")  # Cambia por el nombre de tu pestaña
    rows = worksheet.get_all_values()  # Obtén todas las filas de la hoja
    return len(rows)  # El contador empieza en 1 porque incluye el encabezado


def save_to_google_sheets(data_dict):
    """
    Inserta una nueva fila en la pestaña 'Journal2024' de 'Trades Journal'
    con las celdas en orden (A..T).
    """
    try:
        sh = gc.open("Trades Journal")  # Cambia por el nombre exacto de tu Google Sheet
        worksheet = sh.worksheet("Journal2024")

        existing_data = worksheet.get_all_values()
        if len(existing_data) == 0:
            # Crear encabezados en la fila 1
            cell_list_header = worksheet.range(1, 1, 1, len(FIELDNAMES_ORDER))
            headers = [CSV_HEADERS_MAP[k] for k in FIELDNAMES_ORDER]
            for i, cell in enumerate(cell_list_header):
                cell.value = headers[i]
            worksheet.update_cells(cell_list_header, value_input_option="RAW")

        next_row = len(existing_data) + 1
        row_data = [data_dict.get(k, "") for k in FIELDNAMES_ORDER]

        cell_list = worksheet.range(next_row, 1, next_row, len(FIELDNAMES_ORDER))
        for i, cell in enumerate(cell_list):
            cell.value = row_data[i]

        worksheet.update_cells(cell_list, value_input_option="RAW")

    except Exception as e:
        st.error(f"Error al guardar en Google Sheets: {e}")


###############################################################################
#                    APLICACIÓN STREAMLIT
###############################################################################
trade_count = get_trade_count()

def main():
    global trade_count

    st.title("Mi Journal App (Google Sheets Integrado)")

    current_trade_id = trade_count
    st.write(f"**Trade #:** {current_trade_id}")

    # -------------------------------------------------------------------------
    # 1) DATOS DEL TRADE
    # -------------------------------------------------------------------------
    with st.expander("Datos del Trade"):
        usar_manual = st.checkbox("¿Agregar trades antiguos?")
        if usar_manual:
            manual_date = st.date_input("Fecha del Trade", value=date.today())
            manual_time_str = st.text_input("Hora del Trade (HH:MM)", value="08:00")
            try:
                hh, mm = manual_time_str.split(":")
                hh, mm = int(hh), int(mm)
                manual_datetime_str = f"{manual_date} {hh:02d}:{mm:02d}:00"
            except:
                st.warning("Hora inválida, usando 00:00 por defecto")
                manual_datetime_str = f"{manual_date} 00:00:00"
            final_datetime = manual_datetime_str
        else:
            final_datetime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        st.write(f"**Fecha/Hora final que se guardará**: {final_datetime}")

        pair = st.selectbox("Pair", ["EURUSD", "GBPUSD", "USDJPY", "XAUUSD", "US30", "BTCUSD", "Otro..."])
        trade_type = st.radio("Type", ["Long", "Short"])
        timing = st.selectbox("Timing", ["FFO", "LNO", "MMM1", "MMM2", "NYO", "NYT", "LNC"])
        screenshot_url = st.text_input("Screenshot URL (opcional, p.e. link de TradingView)")

    # -------------------------------------------------------------------------
    # 2) GUARDAR TRADE
    # -------------------------------------------------------------------------
    if st.button("Guardar Trade"):
        data_to_save = {
            "trade_number":         current_trade_id,
            "datetime_final":       final_datetime,
            "pair":                 pair,
            "type":                 trade_type,
            "timing":               timing,
            "screenshot_url":       screenshot_url,
            "timestamp_saved":      datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }

        save_to_google_sheets(data_to_save)
        trade_count += 1
        st.success(f"¡Trade #{current_trade_id} guardado en Google Sheets!")

if __name__ == "__main__":
    main()
