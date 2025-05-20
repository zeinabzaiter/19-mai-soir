import streamlit as st
import pandas as pd
import numpy as np

# Fonction de chargement sécurisé des fichiers Excel ou CSV
def charger_fichier_excel(path):
    try:
        return pd.read_excel(path)
    except Exception as e:
        st.error(f"Erreur de chargement du fichier : {path}\n{e}")
        return pd.DataFrame()

def charger_fichier_csv(path):
    try:
        return pd.read_csv(path)
    except Exception as e:
        st.error(f"Erreur de chargement du fichier : {path}\n{e}")
        return pd.DataFrame()

# Fonction pour détecter les outliers selon Tukey
@st.cache_data
def seuil_tukey(series):
    q1 = series.quantile(0.25)
    q3 = series.quantile(0.75)
    iqr = q3 - q1
    seuil = q3 + 1.5 * iqr
    return seuil

# Chargement des fichiers
df_bacteries = charger_fichier_excel("TOUS les bacteries a etudier.xlsx")
df_autres_ab = charger_fichier_excel("other Antibiotiques staph aureus.xlsx")

st.title("🦠 Tableau de bord ASTER – Surveillance bactérienne")

# Choix de bactérie
if "Category" not in df_bacteries.columns:
    st.error("Colonne 'Category' introuvable dans le fichier TOUS les bacteries a etudier.xlsx.")
else:
    selected_bacteria = st.selectbox("🌿 Bactéries disponibles", df_bacteries["Category"].dropna().unique())

    if selected_bacteria == "Staphylococcus aureus":
        st.subheader("Phénotypes de Staphylococcus aureus")

        if df_autres_ab.empty:
            st.warning("Aucune donnée de résistance disponible.")
        else:
            df = df_autres_ab.copy()

            ab_list = [col for col in df.columns if "% R" in col]
            ab_option = st.selectbox("Choisir un antibiotique", ab_list)

            if ab_option:
                st.write("### Évolution de la résistance :", ab_option)
                st.line_chart(df[["Week", ab_option]].set_index("Week"))

                if "VRSA" in ab_option:
                    df["Alerte"] = df[ab_option].apply(lambda x: 1 if x >= 1 else 0)
                else:
                    seuil = seuil_tukey(df[ab_option])
                    df["Alerte"] = df[ab_option].apply(lambda x: 1 if x > seuil else 0)

                nb_alertes = df["Alerte"].sum()
                st.info(f"Nombre d'alertes : {nb_alertes}")

                if nb_alertes > 0:
                    st.dataframe(df[df["Alerte"] == 1])
