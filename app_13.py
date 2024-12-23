import streamlit as st
import csv
import os
from datetime import datetime, date, time
import matplotlib.pyplot as plt

###############################################################################
#                           CONFIGURACIÓN CSV
###############################################################################
CSV_FILE = "trades_journal.csv"

def get_trade_count():
    """
    Lee el CSV y devuelve cuántos trades se han guardado 
    (asumiendo la primera línea es el header).
    """
    if not os.path.isfile(CSV_FILE):
        return 1
    with open(CSV_FILE, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    return len(lines) if len(lines) > 1 else 1

def save_to_csv(data_dict, filename=CSV_FILE):
    """Guarda data_dict como una nueva fila en el CSV."""
    file_exists = os.path.isfile(filename)
    fieldnames = list(data_dict.keys())
    with open(filename, mode='a', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if not file_exists:
            writer.writeheader()
        writer.writerow(data_dict)

trade_count = get_trade_count()

###############################################################################
#                           APLICACIÓN STREAMLIT
###############################################################################
def main():
    global trade_count

    st.title("Mi Journal App (Secciones + Visualización de KPIs)")

    # Generamos un ID automático para el trade
    current_trade_id = trade_count

    st.write(f"**Trade #:** {current_trade_id}")

    with st.expander("Datos del Trade"):
        # Fecha y hora manual o automática
        usar_manual = st.checkbox("¿Agregar fecha/hora manual?")
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

        # Información básica del trade
        pair = st.selectbox("Pair", ["EURUSD", "GBPUSD", "USDJPY", "XAUUSD", "US30", "BTCUSD", "Otro..."])
        trade_type = st.radio("Type", ["Long", "Short"])
        timing = st.selectbox("Timing", ["FFO", "LNO", "MMM1", "MMM2", "NYO", "NYT", "LNC"])

        # Screenshot URL
        screenshot_url = st.text_input("Screenshot URL (opcional, p.e. link de TradingView)")

    with st.expander("Checklist para las Entradas"):

 # Confluences checklist
        st.write("**Confluences (selecciona las que apliquen)**")
        confluence_list = [
            "Asia: AH - AML - AL",
            "EQH/EQL",
            "Inducement: Liquid",
            "Inducement: Structural",
            "Build up",
            "Mitigation",
            "Daily Cycle",
            "Efficiency of pullback",
            "Entry Helper",
            "Liquidity Equilibrium Touch (LET)",
            "Equilibrium Divergent Mitigation (EDM)",
            "Cup trade",
            "HTF Confirmation",
            "Step Lit (Indent. Liq + Where in cycle + Inducement + rBos)",
            "FBoS",
            "SMT",
            "Timing",
            "Market Structure",
            "Extreme",
            "Last POI w/Imbalance",
            "Decisional",
            "4 entries approach",
            "Previous Day H/L",
            "Previous Week H/L",
            "Day Open"
        ]
        half = len(confluence_list) // 2
        conf_col1 = confluence_list[:half]
        conf_col2 = confluence_list[half:]

        selected_confs_col1 = []
        selected_confs_col2 = []

        col_left, col_right = st.columns(2)
        with col_left:
            for conf in conf_col1:
                check = st.checkbox(conf)
                if check:
                    selected_confs_col1.append(conf)
        with col_right:
            for conf in conf_col2:
                check = st.checkbox(conf)
                if check:
                    selected_confs_col2.append(conf)

        selected_confluences = selected_confs_col1 + selected_confs_col2
        st.write("**Entry Approach #1**")
        approach1_age = st.selectbox("How old is the Inducement?", ["Previous day", "Same day"])
        approach1_type = st.selectbox("What type of Inducement?", ["Liquid Inducement", "Structural Inducement"])
        approach1_m1ibos = st.checkbox("m1 iBoS")
        approach1_valid_poi = st.checkbox("Valid POI + Imbalance?")

        st.write("**Entry Approach #2**")
        approach2_age = st.selectbox("How old is the Inducement?", ["Previous day", "Same day"], key="ap2_age")
        approach2_type = st.selectbox("What type of Inducement?", ["Liquid Inducement", "Structural Inducement"], key="ap2_type")
        approach2_m1ibos = st.checkbox("m1 iBoS", key="ap2_m1ibos")
        approach2_m5_rbos = st.checkbox("m5 rBoS", key="ap2_rbos")
        approach2_valid_poi = st.checkbox("Valid POI + Imbalance?", key="ap2_poi")

        approach3_let = st.checkbox("LET (App#3)?")
        approach4_edm = st.checkbox("EDM (App#4)?")

       

    with st.expander("Resultados y KPIs"):
        result = st.radio("Result", ["Win", "Loss", "BE"])
        comments = st.text_area("Comments sobre el resultado")

        valor_mt5 = st.number_input("Valor en MT5 (equity actual)", value=10000.0, step=100.0)
        delta_percent = ((valor_mt5 - 10000.0) / 10000.0) * 100.0

        st.write(f"**Incremento/Decremento vs los 10k iniciales:** {delta_percent:.2f}%")

        daily_goal_percent = st.number_input("Daily Goal (%)", value=0.7, step=0.1)
        daily_goal = valor_mt5 * (daily_goal_percent / 100)
        st.write(f"**Tu Daily Goal ({daily_goal_percent}% del portafolio)** es: {daily_goal:.2f} USD")

        daily_goal_achieved = st.radio(
            f"¿Se lograron los {daily_goal:.2f} USD del día?", ["Sí", "No"]
        )

        # Visualización de equity mensual
        st.write("### Progreso de Equity Mensual")
        fig, ax = plt.subplots()
        equity_values = [10000, valor_mt5]  # Aquí puedes agregar valores reales de equity
        goal_line = [10000, 10000 * (1 + 0.14)]
        ax.plot(equity_values, marker='o', label="Equity Actual")
        ax.plot(goal_line, linestyle="--", color="green", label="Meta Mensual (14%)")
        ax.set_title("Progreso de Equity")
        ax.set_xlabel("Trades")
        ax.set_ylabel("Equity (USD)")
        ax.legend()
        st.pyplot(fig)

    # Resumen final
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
            "Comentarios": comments,
            "Delta %": delta_percent,
            "Confluences": selected_confluences
        })

    # Botón Guardar
    if st.button("Guardar Trade"):
        data_to_save = {
            "trade_number": current_trade_id,
            "datetime_final": final_datetime,
            "pair": pair,
            "type": trade_type,
            "timing": timing,
            "screenshot_url": screenshot_url,
            "result": result,
            "comments": comments,
            "delta_percent": delta_percent,
            "daily_goal_percent": daily_goal_percent,
            "selected_confluences": "; ".join(selected_confluences),
            "timestamp_saved": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        save_to_csv(data_to_save)
        trade_count += 1
        st.success(f"¡Trade #{current_trade_id} guardado en '{CSV_FILE}'!")

if __name__ == "__main__":
    main()
