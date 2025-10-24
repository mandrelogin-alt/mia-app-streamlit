import streamlit as st
import pandas as pd
import numpy as np

# --- Configurazione Pagina ---
# Imposta il titolo che appare nella scheda del browser
st.set_page_config(
    page_title="La Mia Prima App",
    page_icon="🚀",
    layout="wide"
)

# --- Titolo Principale ---
st.title('Benvenuto nella mia prima App Streamlit! 🎈')
st.write('Questa app è ospitata su Streamlit Community Cloud.')

# --- Widget Interattivi (in una Sidebar) ---
st.sidebar.header('Configura qui le tue opzioni:')

# Slider numerico
eta = st.sidebar.slider(
    'Seleziona la tua età:', 
    min_value=0, 
    max_value=100, 
    value=25,
    step=1
)

st.sidebar.write(f"Hai selezionato {eta} anni.")

# Input di testo
nome_utente = st.sidebar.text_input(
    'Come ti chiami?', 
    'Visitatore'
)

st.header(f'Ciao, {nome_utente}!')
st.write(f'La tua età è {eta}.')


# --- Contenuto Principale (Grafici e Dati) ---
st.header('Dati e Grafici di Esempio')

# Checkbox per mostrare/nascondere elementi
if st.checkbox('Mostra un grafico a linee di esempio'):
    st.subheader('Grafico a Linee')
    # Creiamo dati casuali per il grafico
    chart_data = pd.DataFrame(
        np.random.randn(20, 3),
        columns=['a', 'b', 'c']
    )
    st.line_chart(chart_data)

if st.checkbox('Mostra un DataFrame di esempio'):
    st.subheader('Tabella Dati')
    # Creiamo un DataFrame pandas
    df = pd.DataFrame(
        np.random.randn(10, 3),  # 10 righe, 3 colonne
        columns=['Colonna 1', 'Colonna 2', 'Colonna 3']
    )
    st.dataframe(df)

st.balloons() # Un piccolo festeggiamento!
