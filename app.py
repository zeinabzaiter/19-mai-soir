import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np

st.set_page_config(page_title="Tableau de bord ASTER", layout="wide")
st.title("Tableau de bord ASTER – Surveillance bactérienne")

# Chargement des données
@st.cache_data
def load_data():
    bacteries_df = pd.read_excel("TOUS_les_bacteries_a_etudier.xlsx")
    staph_df = pd.read_excel("staph_aureus_hebdomadaire.xlsx")
    tests_df = pd.read_csv("tests_par_semaine_antibiotiques_2024.csv")
    other_df = pd.read_excel("other_Antibiotiques_staph_aureus.xlsx")
    pheno_df = pd.read_excel("staph_aureus_pheno_final.xlsx")
    return bacteries_df, staph_df, tests_df, other_df, pheno_df

bacteries_df, staph_df, tests_df, other_df, pheno_df = load_data()

# ---- Sélection de la bactérie ----
bacteria_list = bacteries_df['Category'].unique()
selected_bacteria = st.selectbox("Bactéries disponibles", bacteria_list)

# ---- Création des onglets ----
tabs = st.tabs(["Alertes par service", "Évolution résistance", "Phénotypes"])

# ---- Onglet 1 : Alertes ----
with tabs[0]:
    st.header(f"Analyse : {selected_bacteria}")

    if selected_bacteria == "Staphylococcus aureus":
        df = staph_df
        ab_columns = [col for col in df.columns if col not in ["DATE_ENTREE", "LIBELLE_DEMANDEUR"]]

        # Calcul des alertes sauf pour Vancomycine (VRSA)
        alertes = []
        for ab in ab_columns:
            if ab == "Vancomycine":
                count_vrsa = (df[ab] == "R").sum()
                alertes.append({"Antibiotique": ab, "Alertes": count_vrsa})
            else:
                freq = df.groupby("LIBELLE_DEMANDEUR")[ab].apply(lambda x: (x == "R").mean() * 100)
                q3 = np.percentile(freq, 75)
                iqr = q3 - np.percentile(freq, 25)
                seuil = q3 + 1.5 * iqr
                n_alertes = (freq > seuil).sum()
                alertes.append({"Antibiotique": ab, "Alertes": n_alertes})

        alertes_df = pd.DataFrame(alertes)
        st.dataframe(alertes_df)
    else:
        st.warning("Données non disponibles pour cette bactérie.")

# ---- Onglet 2 : Evolution résistance ----
with tabs[1]:
    st.header(f"Évolution des résistances par antibiotique")
    if selected_bacteria == "Staphylococcus aureus":
        ab_option = st.selectbox("Choisir un antibiotique :", other_df.columns[1:])
        df = other_df[["Semaine", ab_option]].dropna()
        y_col = ab_option

        if not df.empty:
            fig = px.line(df, x="Semaine", y=y_col, title=f"% Résistance à {ab_option}")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.error(f"Aucune donnée disponible pour {ab_option}")
    else:
        st.warning("Section disponible uniquement pour Staphylococcus aureus.")

# ---- Onglet 3 : Phénotypes ----
with tabs[2]:
    st.header("Phénotypes (alerte si VRSA ≥ 1)")
    if selected_bacteria == "Staphylococcus aureus":
        df = pheno_df.copy()
        if "week" not in df.columns:
            st.error("Colonne 'week' manquante dans le fichier.")
        else:
            df["week"] = pd.to_datetime(df["week"])
            df_vrsa = df[df["Vancomycine"] == "R"]
            if not df_vrsa.empty:
                st.dataframe(df_vrsa)
            else:
                st.success("Aucune alerte VRSA détectée.")
    else:
        st.warning("Phénotypes uniquement disponibles pour Staphylococcus aureus.")
