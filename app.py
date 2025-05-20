
import streamlit as st
import pandas as pd

# Chargement des données
@st.cache_data
def load_data():
    try:
        df = pd.read_excel("TOUS les bacteries a etudier.xlsx")
    except Exception as e:
        st.error(f"Erreur lors du chargement : {e}")
        return pd.DataFrame()
    return df

bacteries_df = load_data()

# Vérifier la présence de la colonne 'Espece' (sans accent)
col_name = next((col for col in bacteries_df.columns if "espec" in col.lower()), None)

if col_name is None:
    st.error("Colonne 'Espèce' introuvable dans le fichier.")
else:
    selected_bacteria = st.selectbox("🦠 Bactéries disponibles", bacteries_df[col_name].unique())
    st.write(f"Vous avez sélectionné : **{selected_bacteria}**")
    st.dataframe(bacteries_df[bacteries_df[col_name] == selected_bacteria])
