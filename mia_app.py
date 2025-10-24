import streamlit as st
import pandas as pd
import plotly.express as px
from statsmodels.tsa.holtwinters import ExponentialSmoothing
import io # Per la gestione I/O in memoria per l'export Excel
from openpyxl import Workbook # Importato anche se pandas lo usa 'sottobanco'

# --- Configurazione Pagina ---
# Usiamo il layout "wide" per un look più moderno
st.set_page_config(layout="wide", page_title="Previsione Domanda", page_icon="📈")

# --- Stile CSS Moderno (Opzionale ma consigliato) ---
# Iniettiamo un po' di CSS per migliorare l'aspetto
st.markdown("""
<style>
    /* Stile per i container principali */
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
        padding-left: 5rem;
        padding-right: 5rem;
    }
    /* Stile per la sidebar */
    .stSidebar {
        background-color: #f0f2f6;
    }
    /* Stile per i bottoni (es. download) */
    .stDownloadButton > button {
        background-color: #007bff;
        color: white;
        border: none;
        padding: 0.5rem 1rem;
        border-radius: 0.3rem;
        font-weight: bold;
        cursor: pointer;
    }
    .stDownloadButton > button:hover {
        background-color: #0056b3;
    }
    /* Stile per i "card" con st.container */
    .st-emotion-cache-z5fcl4 {
        border-radius: 10px;
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        padding: 1.5rem;
        background-color: #ffffff;
        margin-bottom: 1rem;
    }
</style>
""", unsafe_allow_html=True)

# --- Funzione per convertire DataFrame in Excel in memoria ---
@st.cache_data # Cache per performance
def to_excel(df):
    """
    Converte un DataFrame in un file Excel in memoria (BytesIO).
    """
    output = io.BytesIO()
    # Usiamo 'openpyxl' come engine, che è necessario aver installato
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=True, sheet_name='Previsione')
    processed_data = output.getvalue()
    return processed_data

# --- Funzione per caricare e preparare i dati ---
@st.cache_data # Cache per non ricaricare il file ad ogni interazione
def load_data(uploaded_file):
    """
    Carica il CSV, converte le date e imposta l'indice.
    """
    try:
        df = pd.read_csv(uploaded_file, parse_dates=['data'])
        df.set_index('data', inplace=True)
        df.sort_index(inplace=True)
        return df
    except Exception as e:
        st.error(f"Errore nel caricamento del file: {e}")
        return None

# --- Titolo dell'App ---
st.title("📈 Dashboard di Previsione della Domanda")
st.markdown("Utilizza questa app per analizzare serie storiche e creare previsioni con il metodo Holt-Winters.")

# --- Sidebar per Input Utente ---
st.sidebar.header("Impostazioni di Analisi")
uploaded_file = st.sidebar.file_uploader("Carica il tuo file CSV", type=["csv"])

if uploaded_file is None:
    st.info("Per favore, carica un file CSV per iniziare l'analisi.", icon="☝️")
    # Puoi inserire qui il caricamento del file di default se lo aggiungi alla repo
    # st.text("In alternativa, uso il file 'serie_storica_ordinato.csv' di default.")
    # try:
    #     df = load_data("serie_storica_ordinato.csv")
    # except FileNotFoundError:
    #     st.stop()
    st.stop()


# --- Logica Principale (se il file è caricato) ---
df = load_data(uploaded_file)

if df is not None:
    # Selezione dell'Item
    item_list = df['item'].unique()
    selected_item = st.sidebar.selectbox("Seleziona un 'Item' da analizzare:", item_list)
    
    # Parametri per la Previsione
    st.sidebar.subheader("Parametri di Previsione")
    periods_to_forecast = st.sidebar.slider("Mesi da prevedere:", min_value=1, max_value=36, value=12, step=1)
    
    # Parametri Holt-Winters
    st.sidebar.subheader("Parametri Holt-Winters")
    seasonal_periods = st.sidebar.number_input("Periodi Stagionali (es. 12 per mensile):", min_value=1, value=12)
    trend_type = st.sidebar.selectbox("Tipo di Trend:", ['add', 'mul', None], index=0, format_func=lambda x: str(x) if x else "None")
    seasonal_type = st.sidebar.selectbox("Tipo di Stagionalità:", ['add', 'mul', None], index=0, format_func=lambda x: str(x) if x else "None")

    # --- Preparazione Dati Specifici per l'Item ---
    st.header(f"Analisi per l'Item: {selected_item}")

    with st.container():
        st.subheader("Preparazione Dati Storici")
        
        # Filtra i dati per l'item selezionato
        item_data = df[df['item'] == selected_item]['quantità']
        
        # Aggregazione: Holt-Winters richiede dati a frequenza fissa.
        # Aggreghiamo i dati giornalieri/irregolari in mensili (somma).
        # 'MS' = Month Start (inizio mese)
        monthly_data = item_data.resample('MS').sum().fillna(0)
        
        st.markdown(f"""
        I dati originali sono stati aggregati su base **mensile** (sommando le `quantità`)
        per poter applicare il modello Holt-Winters, che richiede una frequenza temporale fissa.
        """)
        st.dataframe(monthly_data.head())

        # Controllo se ci sono abbastanza dati
        if len(monthly_data) < 2 * seasonal_periods:
            st.warning(f"Attenzione: i dati storici ({len(monthly_data)} mesi) sono insufficienti per una stagionalità di {seasonal_periods} periodi. Il modello potrebbe fallire o essere inaccurato.")
            st.stop()


    # --- Grafico Dati Storici ---
    with st.container():
        st.subheader("Grafico Dati Storici (Aggregati Mensili)")
        fig_hist = px.line(monthly_data, x=monthly_data.index, y='quantità', 
                           title=f"Domanda Storica Mensile per {selected_item}",
                           labels={'quantità': 'Quantità Totale Mensile', 'data': 'Data'})
        fig_hist.update_layout(hovermode="x unified")
        st.plotly_chart(fig_hist, use_container_width=True)


    # --- Esecuzione Modello e Previsione ---
    with st.container():
        st.subheader("Risultati della Previsione")
        try:
            # Inizializzazione e Fit del modello
            model = ExponentialSmoothing(
                monthly_data,
                trend=trend_type,
                seasonal=seasonal_type,
                seasonal_periods=seasonal_periods,
                initialization_method="estimated" # Metodo robusto
            )
            
            fit = model.fit()
            
            # Creazione della previsione
            forecast = fit.forecast(periods_to_forecast)
            
            # Arrotondamento previsioni (non si possono vendere 0.5 prodotti)
            forecast = forecast.apply(lambda x: max(0, round(x)))
            
            # --- Preparazione Dati per Grafico e Download ---
            
            # Rinomina la serie per il grafico
            forecast.name = "Previsione"
            monthly_data.name = "Dati Storici"

            # Combina dati storici e previsione per il plot
            df_plot = pd.concat([monthly_data, forecast], axis=1)
            
            # Creazione Grafico Previsione
            fig_forecast = px.line(df_plot, 
                                   title=f"Previsione vs Dati Storici per {selected_item}",
                                   labels={'value': 'Quantità', 'data': 'Data'})
            
            # Aggiungi stili diversi per le linee
            fig_forecast.update_traces(selector={"name": "Previsione"}, line=dict(dash='dot', width=3))
            fig_forecast.update_traces(selector={"name": "Dati Storici"}, line=dict(width=2))
            fig_forecast.update_layout(hovermode="x unified")
            
            st.plotly_chart(fig_forecast, use_container_width=True)
            
            
            # --- Sezione Download ---
            st.subheader("Download Dati di Previsione")
            
            # Prepara il DataFrame per l'Excel
            forecast_df_download = forecast.to_frame()
            forecast_df_download.index.name = "Data"
            
            st.dataframe(forecast_df_download)
            
            # Converti in file Excel in memoria
            excel_data = to_excel(forecast_df_download)
            
            st.download_button(
                label="📥 Scarica Previsione (Excel)",
                data=excel_data,
                file_name=f"previsione_domanda_{selected_item}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

        except Exception as e:
            st.error(f"Errore durante l'esecuzione del modello Holt-Winters: {e}")
            st.markdown("Prova a cambiare i parametri (es. Trend, Stagionalità o Periodi Stagionali). Spesso questo errore accade se i dati non hanno stagionalità o trend, prova a impostarli su `None`.")
