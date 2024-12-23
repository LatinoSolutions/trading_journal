import streamlit as st
import csv
import os
from datetime import datetime, date
import matplotlib.pyplot as plt

# -----------------------
# INTEGRACIÓN GOOGLE SHEETS
# -----------------------
import gspread
from google.oauth2.service_account import Credentials

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]
credentials = Credentials.from_service_account_file(
    "credentials.json",  # <--- Ajusta la ruta real de tu JSON
    scopes=SCOPES
)
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
#                     FUNCIONES PARA CSV Y GOOGLE SHEETS
###############################################################################
CSV_FILE = "trades_journal.csv"

def get_trade_count():
    """Lee el CSV y devuelve cuántos trades se han guardado."""
    if not os.path.isfile(CSV_FILE):
        return 1
    with open(CSV_FILE, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    return len(lines) if len(lines) > 1 else 1

def save_to_csv(data_dict):
    """Guarda data_dict como nueva fila en el CSV, con orden y cabeceras fijas."""
    file_exists = os.path.isfile(CSV_FILE)

    row_to_write = {}
    for key in FIELDNAMES_ORDER:
        row_to_write[CSV_HEADERS_MAP[key]] = data_dict.get(key, "")

    csv_headers = [CSV_HEADERS_MAP[k] for k in FIELDNAMES_ORDER]

    with open(CSV_FILE, mode='a', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=csv_headers)
        if not file_exists:
            writer.writeheader()
        writer.writerow(row_to_write)

def save_to_google_sheets(data_dict):
    """
    Inserta una nueva fila en la pestaña 'Journal2024' de 'Trades Journal'
    con las celdas en orden (A..T).
    """
    try:
        sh = gc.open("Trades Journal")  # <--- Cambia por el nombre EXACTO de tu Google Sheet
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

    st.title("Bru's Journal App!🥃")

    current_trade_id = trade_count
    st.write(f"**Trade #:** {current_trade_id}")

    # -------------------------------------------------------------------------
    # 1) DATOS DEL TRADE
    # -------------------------------------------------------------------------
    with st.expander("Datos del Trade"):
        usar_manual = st.checkbox("¿Agregar un trade antiguo?")
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
    # 2) CHECKLIST DE ENTRADAS (CONFLUENCIAS + APPROACHES)
    # -------------------------------------------------------------------------
    with st.expander("Checklist para las Entradas"):
        st.write("**Confluences (selecciona todas las que apliquen)**")
        confluence_list = [
            "Asia: High", "Asia: MidLine", "Asia: Low", "EQH", "EQL",
            "Inducement: minor", "Inducement: Medium", "Inducement: Major",
            "Inducement: Liquid", "Inducement: Structural", "Build up",
            "Mitigation", "Daily Cycle", "Efficiency of pullback", "Entry Helper",
            "Liquidity Equilibrium Touch (LET)", "Equilibrium Divergent Mitigation (EDM)",
            "Cup trade", "FBoS", "SMT", "Timing", "Extreme POI",
            "Last POI w/Imbalance", "Decisional", "Previous Day High", "Previous Day Low",
            "Previous Week High", "Previous Week Low", "Day Open",
            "Entry Approach #1", "Entry Approach #2", "Entry Approach #3", "Entry Approach #4",
        ]
        half = len(confluence_list) // 2
        conf_col1, conf_col2 = confluence_list[:half], confluence_list[half:]

        selected_confs_col1, selected_confs_col2 = [], []
        col_left, col_right = st.columns(2)
        with col_left:
            for conf in conf_col1:
                if st.checkbox(conf):
                    selected_confs_col1.append(conf)
        with col_right:
            for conf in conf_col2:
                if st.checkbox(conf):
                    selected_confs_col2.append(conf)
        selected_confluences = selected_confs_col1 + selected_confs_col2
        confluences_count = len(selected_confluences)

        # ---------------------------------------------------------------------
        # APPROACH 1
        # ---------------------------------------------------------------------
        st.markdown("### Approach #1")

        approach1_used = st.radio("¿Se usó Approach #1 en este trade?", ["No", "Sí"], index=0)
        approach1_age = st.selectbox("¿Previous Day o Same Day? (App#1)", 
                                     ["Previous day", "Same day"])
        approach1_type = st.selectbox("¿Structural o Liquid Inducement? (App#1)",
                                      ["Structural Inducement", "Liquid Inducement"])
        approach1_m1ibos = st.checkbox("m1 iBoS (App#1)")
        approach1_valid_poi = st.checkbox("Valid POI + Imbalance? (App#1)")

        approach1_data = (
            f"Used={approach1_used}, "
            f"Age={approach1_age}, "
            f"Type={approach1_type}, "
            f"m1IBoS={approach1_m1ibos}, "
            f"ValidPOI={approach1_valid_poi}"
        )

        # ---------------------------------------------------------------------
        # APPROACH 2
        # ---------------------------------------------------------------------
        st.markdown("### Approach #2")

        approach2_used = st.radio("¿Se usó Approach #2 en este trade?", ["No", "Sí"], index=0)
        approach2_age = st.selectbox("¿Previous Day o Same Day? (App#2)",
                                     ["Previous day", "Same day"])
        approach2_type = st.selectbox("¿Structural o Liquid Inducement? (App#2)",
                                      ["Structural Inducement", "Liquid Inducement"])
        approach2_mitigable = st.checkbox("¿El Inducement dejó Zona Mitigable? (App#2)")
        approach2_m1ibos = st.checkbox("m1 iBoS (App#2)")
        approach2_m5_rbos = st.checkbox("m5 rBoS (App#2)")

        approach2_data = (
            f"Used={approach2_used}, "
            f"Age={approach2_age}, "
            f"Type={approach2_type}, "
            f"ZonaMitigable={approach2_mitigable}, "
            f"m1IBoS={approach2_m1ibos}, "
            f"m5rBoS={approach2_m5_rbos}"
        )

        # ---------------------------------------------------------------------
        # APPROACH 3
        # ---------------------------------------------------------------------
        st.markdown("### Approach #3 (LET)")

        approach3_used = st.radio("¿Se usó Approach #3 en este trade?", ["No", "Sí"], index=0)
        approach3_a1_ready = st.checkbox("¿Approach 1 listo? (App#3)")
        approach3_a2_ready = st.checkbox("¿Approach 2 listo? (App#3)")
        approach3_let_entry = st.checkbox("LET ENTRY (App#3)")

        approach3_data = (
            f"Used={approach3_used}, "
            f"A1Ready={approach3_a1_ready}, "
            f"A2Ready={approach3_a2_ready}, "
            f"LET={approach3_let_entry}"
        )

        # ---------------------------------------------------------------------
        # APPROACH 4
        # ---------------------------------------------------------------------
        st.markdown("### Approach #4 (EDM)")

        approach4_used = st.radio("¿Se usó Approach #4 en este trade?", ["No", "Sí"], index=0)
        approach4_a1_ready = st.checkbox("¿Approach 1 listo? (App#4)")
        approach4_a2_ready = st.checkbox("¿Approach 2 listo? (App#4)")
        approach4_a3_ready = st.checkbox("¿Approach 3 listo? (App#4)")
        approach4_edm_entry = st.checkbox("EDM ENTRY (App#4)")

        approach4_data = (
            f"Used={approach4_used}, "
            f"A1Ready={approach4_a1_ready}, "
            f"A2Ready={approach4_a2_ready}, "
            f"A3Ready={approach4_a3_ready}, "
            f"EDM={approach4_edm_entry}"
        )

    # -------------------------------------------------------------------------
    # 3) RESULTADOS Y KPIs
    # -------------------------------------------------------------------------
    with st.expander("Resultados y KPIs"):
        pnl_usd = st.number_input("¿Cuántos USD se ganaron o perdieron?", value=0.0, step=50.0)
        result = st.radio("Result", ["Win", "Loss", "BE"])
        comments = st.text_area("Comments sobre el resultado")

        valor_mt5 = st.number_input("Valor en MT5 (equity actual)", value=10000.0, step=100.0)
        if result == "Win":
            new_equity = valor_mt5 + abs(pnl_usd)
        elif result == "Loss":
            new_equity = valor_mt5 - abs(pnl_usd)
        else:
            new_equity = valor_mt5

        st.write(f"**Equity tras aplicar el resultado:** {new_equity:.2f} USD")

        delta_percent = ((new_equity - 10000.0) / 10000.0) * 100.0
        st.write(f"**Incremento/Decremento vs los 10k iniciales:** {delta_percent:.2f}%")

        daily_goal_percent = st.number_input("Daily Goal (%)", value=0.7, step=0.1)
        if result == "Loss":
            daily_goal_percent = 0.7
            st.warning("Por ser pérdida, se fuerza el Daily Goal al 0.7%.")
            daily_goal = new_equity * (daily_goal_percent / 100) + abs(pnl_usd)
            st.info(f"Se añade la pérdida de {abs(pnl_usd):.2f} USD al {daily_goal_percent}% de {new_equity:.2f} USD.")
        else:
            daily_goal = new_equity * (daily_goal_percent / 100)

        st.write(f"**Tu Daily Goal ({daily_goal_percent}% del portafolio)** es: {daily_goal:.2f} USD")

        daily_goal_achieved = st.radio(
            f"¿Se lograron los {daily_goal:.2f} USD del día?", ["Sí", "No"]
        )

        # Visualización de equity mensual
        st.write("### Progreso de Equity Mensual")
        fig, ax = plt.subplots()
        equity_values = [10000, new_equity]
        goal_line = [10000, 10000 * (1 + 0.14)]
        ax.plot(equity_values, marker='o', label="Equity Actual")
        ax.plot(goal_line, linestyle="--", color="green", label="Meta Mensual (14%)")
        ax.set_title("Progreso de Equity")
        ax.set_xlabel("Trades")
        ax.set_ylabel("Equity (USD)")
        ax.legend()
        st.pyplot(fig)

        monthly_goal_value = 10000 * 1.14
        monthly_diff_usd = monthly_goal_value - new_equity
        if monthly_diff_usd < 0:
            st.success("¡Ya has superado la meta mensual!")
            monthly_diff_usd = 0
        else:
            st.write(f"Te faltan {monthly_diff_usd:.2f} USD para la meta mensual de 11400 USD.")

        total_gap = monthly_goal_value - 10000
        if total_gap > 0:
            monthly_diff_percent = (monthly_diff_usd / total_gap) * 100
            st.write(f"Estás a un {monthly_diff_percent:.2f}% de cumplir la meta mensual.")
        else:
            st.write("La meta mensual parece ser menor o igual al capital base (revisa configuración).")

    # -------------------------------------------------------------------------
    # 4) RESUMEN FINAL
    # -------------------------------------------------------------------------
    st.subheader("Resumen del Trade")
    if st.button("Mostrar Resumen"):
        st.write({
            "Trade ID": current_trade_id,
            "Datetime": final_datetime,
            "Pair": pair,
            "Type": trade_type,
            "Timing": timing,
            "Screenshot URL": screenshot_url,
            "Result": result,
            "PnL (USD)": pnl_usd,
            "Comentarios": comments,
            "Equity final": new_equity,
            "Delta % vs 10k": delta_percent,
            "Confluences": selected_confluences,
            "Confluence Count": confluences_count,
            "Approach1 Data": approach1_data,
            "Approach2 Data": approach2_data,
            "Approach3 Data": approach3_data,
            "Approach4 Data": approach4_data
        })

    # -------------------------------------------------------------------------
    # 5) GUARDAR TRADE
    # -------------------------------------------------------------------------
    if st.button("Guardar Trade"):
        data_to_save = {
            "trade_number":         current_trade_id,
            "datetime_final":       final_datetime,
            "pair":                 pair,
            "type":                 trade_type,
            "timing":               timing,
            "screenshot_url":       screenshot_url,
            "result":               result,
            "pnl_usd":              pnl_usd,
            "new_equity":           new_equity,
            "comments":             comments,
            "delta_percent":        delta_percent,
            "daily_goal_percent":   daily_goal_percent,
            "daily_goal_value":     daily_goal,
            "selected_confluences": "; ".join(selected_confluences),
            "confluences_count":    confluences_count,
            "approach1_data":       approach1_data,
            "approach2_data":       approach2_data,
            "approach3_data":       approach3_data,
            "approach4_data":       approach4_data,
            "timestamp_saved":      datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

        save_to_csv(data_to_save)
        save_to_google_sheets(data_to_save)

        trade_count += 1
        st.success(f"¡Trade #{current_trade_id} guardado en '{CSV_FILE}' y en Google Sheets!")

if __name__ == "__main__":
    main()
