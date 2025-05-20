import streamlit as st
import pandas as pd
import plotly.express as px

def load_data():
    # Chargement des fichiers
    bacteria_df = pd.read_excel("TOUS les bacteries a etudier.xlsx")
    staph_weekly_df = pd.read_excel("staph aureus hebdomadaire excel.xlsx")
    tests_df = pd.read_csv("tests_par_semaine_antibiotiques_2024.csv")
    other_ab_df = pd.read_excel("other Antibiotiques staph aureus.xlsx")
    pheno_df = pd.read_excel("staph_aureus_pheno_final.xlsx")

    # Harmonisation des noms de colonnes
    if 'Category' in bacteria_df.columns:
        bacteria_df.rename(columns={'Category': 'Espece'}, inplace=True)

    return bacteria_df, staph_weekly_df, tests_df, other_ab_df, pheno_df

# Appel des données
bacteria_df, staph_df, tests_df, other_ab_df, pheno_df = load_data()

# Interface Streamlit
st.set_page_config(page_title="Dashboard ASTER", layout="wide")
st.title("Tableau de bord ASTER – Surveillance bactérienne")

# Sélecteur de bactérie
if "Espece" not in bacteria_df.columns:
    st.error("Colonne 'Espèce' introuvable dans le fichier.")
    st.stop()

selected_bacteria = st.selectbox("Bactéries disponibles", bacteria_df["Espece"].unique())
st.header(f"Analyse : {selected_bacteria}")

# Onglets
onglet = st.tabs(["Alertes par service", "Évolution résistance", "Phénotypes"])

with onglet[0]:
    st.subheader("Alertes par service")
    if selected_bacteria == "Staphylococcus aureus":
        alert_df = staph_df
    else:
        alert_df = bacteria_df[bacteria_df["Espece"] == selected_bacteria]

    st.dataframe(alert_df)

with onglet[1]:
    st.subheader("Évolution des résistances par antibiotique")
    if selected_bacteria == "Staphylococcus aureus":
        ab_option = st.selectbox("Choisir un antibiotique :", tests_df.columns.drop("Semaine"))
        if ab_option in tests_df.columns:
            df = tests_df[["Semaine", ab_option]].dropna()
            if not df.empty:
                fig = px.line(df, x="Semaine", y=ab_option, title=f"% Résistance à {ab_option}")
                st.plotly_chart(fig)
            else:
                st.warning(f"Aucune donnée disponible pour {ab_option}")
        else:
            st.warning("Antibiotique non disponible dans le fichier.")
    else:
        st.warning("Visualisation réservée pour Staphylococcus aureus.")

with onglet[2]:
    st.subheader("Phénotypes (alerte si VRSA ≥ 1)")
    if selected_bacteria == "Staphylococcus aureus":
        if not pheno_df.empty:
            try:
                pheno_df["week"] = pd.to_datetime(pheno_df["week"], errors='coerce')
                st.dataframe(pheno_df)
            except Exception as e:
                st.error(f"Erreur de traitement des dates : {e}")
        else:
            st.warning("Aucune donnée de phénotypes disponible.")
    else:
        st.warning("Visualisation réservée pour Staphylococcus aureus.")
