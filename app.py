import streamlit as st
import pandas as pd
import plotly.express as px

# ========== Chargement des données ==========
@st.cache_data
def load_data():
    bacteries_df = pd.read_excel("TOUS_les_bacteries_a_etudier.xlsx")
    bacteries_df.columns = bacteries_df.columns.str.strip()

    staph_df = pd.read_excel("staph_aureus_hebdomadaire.xlsx")
    tests_df = pd.read_csv("tests_par_semaine_antibiotiques_2024.csv")
    other_df = pd.read_excel("other_Antibiotiques_staph_aureus.xlsx")
    pheno_df = pd.read_excel("staph_aureus_pheno_final.xlsx")

    return bacteries_df, staph_df, tests_df, other_df, pheno_df

bacteries_df, staph_df, tests_df, other_df, pheno_df = load_data()

# ========== Titre principal ==========
st.title("Tableau de bord ASTER – Surveillance bactérienne")

# ========== Choix de bactérie ==========
selected_bacteria = st.selectbox("Bactéries disponibles", bacteries_df["Espece"].unique())

st.markdown(f"## Analyse : {selected_bacteria}")
tabs = st.tabs(["Alertes par service", "Évolution résistance", "Phénotypes"])

# ========== Onglet 1 : Alertes par service ==========
with tabs[0]:
    st.subheader("Alertes hebdomadaires par service")
    if selected_bacteria == "Staphylococcus aureus":
        alertes = staph_df[staph_df["Alerte"] == 1]
        grouped = alertes.groupby(["Service", "Semaine"]).size().reset_index(name="Nombre d'alertes")

        fig = px.scatter(grouped, x="Semaine", y="Service", size="Nombre d'alertes", color="Nombre d'alertes",
                         title="Alertes Staphylococcus aureus par semaine et service")
        st.plotly_chart(fig)
    else:
        st.info("Données d'alerte non disponibles pour cette bactérie.")

# ========== Onglet 2 : Évolution de la résistance ==========
with tabs[1]:
    st.subheader("Évolution des résistances par antibiotique")
    if selected_bacteria == "Staphylococcus aureus":
        ab_option = st.selectbox("Choisir un antibiotique :", tests_df.columns[1:])
        df = tests_df[["Semaine", ab_option]]

        if df[ab_option].dropna().empty:
            st.warning(f"Aucune donnée disponible pour {ab_option}")
        else:
            fig = px.line(df, x="Semaine", y=ab_option, title=f"% Résistance à {ab_option}")
            st.plotly_chart(fig)
    else:
        st.info("Données d'antibiogramme non disponibles pour cette bactérie.")

# ========== Onglet 3 : Phénotypes ==========
with tabs[2]:
    st.subheader("Phénotypes (alerte si VRSA ≥ 1)")
    if selected_bacteria == "Staphylococcus aureus":
        if "week" in pheno_df.columns:
            pheno_df["week"] = pd.to_datetime(pheno_df["week"], errors='coerce')
            pheno_df.dropna(subset=["week"], inplace=True)
            vrsa_alerts = pheno_df[pheno_df["VRSA"] >= 1]

            if not vrsa_alerts.empty:
                fig = px.scatter(vrsa_alerts, x="week", y="Service", color="VRSA", size="VRSA",
                                 title="Alertes VRSA par semaine et service")
                st.plotly_chart(fig)
            else:
                st.info("Aucune alerte VRSA détectée.")
        else:
            st.warning("Colonne 'week' manquante dans les données de phénotype.")
    else:
        st.info("Phénotypes non disponibles pour cette bactérie.")
