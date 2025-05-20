import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

# ======== Chargement des données ========
@st.cache_data
def load_data():
    bacteries_df = pd.read_excel("TOUS_les_bacteries_a_etudier.xlsx")
    staph_df = pd.read_excel("staph_aureus_hebdomadaire.xlsx")
    tests_df = pd.read_csv("tests_par_semaine_antibiotiques_2024.csv")
    other_df = pd.read_excel("other_Antibiotiques_staph_aureus.xlsx")
    pheno_df = pd.read_excel("staph_aureus_pheno_final.xlsx")
    return bacteries_df, staph_df, tests_df, other_df, pheno_df

bacteries_df, staph_df, tests_df, other_df, pheno_df = load_data()

# ======== Sélection de la bactérie ========
col_name = next((col for col in bacteries_df.columns if "espec" in col.lower()), None)
if not col_name:
    st.error("Colonne 'Espèce' introuvable dans le fichier.")
    st.stop()

selected_bacteria = st.selectbox("🦠 Bactéries disponibles", bacteries_df[col_name].unique())
st.title(f"Analyse : {selected_bacteria}")

# ======== Tabs ========
tabs = st.tabs(["Alertes par service", "Évolution résistance", "Phénotypes"])

# ======== Tab 1: Alertes par service ========
with tabs[0]:
    st.subheader("Alertes par service")
    data = bacteries_df[bacteries_df[col_name] == selected_bacteria]

    def detect_alerts(values, ab_name):
        if ab_name.lower() in ["vancomycine", "vrsa"]:
            return values >= 1
        q1 = np.percentile(values, 25)
        q3 = np.percentile(values, 75)
        iqr = q3 - q1
        seuil = q3 + 1.5 * iqr
        return values > seuil

    ab_cols = [col for col in data.columns if col not in ["Date", col_name]]
    for ab in ab_cols:
        values = data[ab].fillna(0)
        alertes = detect_alerts(values, ab)
        st.write(f"🔬 Antibiotique : **{ab}**")
        st.dataframe(data[alertes])

# ======== Tab 2: Évolution résistance ========
with tabs[1]:
    st.subheader("Évolution des résistances par antibiotique")
    st.markdown("Choisir un antibiotique :")

    ab_options = [col for col in tests_df.columns if col not in ["Semaine"]]
    ab_option = st.selectbox("Antibiotique", ab_options)

    if ab_option in tests_df.columns:
        df = tests_df[["Semaine", ab_option]].rename(columns={ab_option: "Résistance (%)"})
        fig = px.line(df, x="Semaine", y="Résistance (%)", title=f"Évolution de la résistance à {ab_option}")
        st.plotly_chart(fig)
    else:
        st.warning(f"Aucune donnée disponible pour {ab_option}")

# ======== Tab 3: Phénotypes ========
with tabs[2]:
    st.subheader("Phénotypes (alerte si VRSA ≥ 1)")

    if not pheno_df.empty:
        if "week" in pheno_df.columns:
            pheno_df["week"] = pd.to_datetime(pheno_df["week"], errors='coerce')
        st.dataframe(pheno_df)

        if "week" in pheno_df.columns and "VRSA" in pheno_df.columns:
            alerts = pheno_df[pheno_df["VRSA"] >= 1]
            if not alerts.empty:
                st.warning("🚨 Alerte(s) détectée(s) pour VRSA :")
                st.dataframe(alerts)
            else:
                st.success("Aucune alerte VRSA détectée.")
    else:
        st.info("Aucune donnée de phénotypes disponible.")
