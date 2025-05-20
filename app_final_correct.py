
import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Dashboard ASTER", layout="wide")

@st.cache_data
def load_data():
    bacteries_df = pd.read_excel("TOUS_les_bacteries_a_etudier.xlsx")
    staph_df = pd.read_excel("staph_aureus_hebdomadaire.xlsx")
    tests_df = pd.read_csv("tests_par_semaine_antibiotiques_2024.csv")
    other_df = pd.read_excel("other Antibiotiques staph aureus.xlsx")
    pheno_df = pd.read_excel("staph_aureus_pheno_final.xlsx")
    return bacteries_df, staph_df, tests_df, other_df, pheno_df

def detect_outliers(df, col):
    q1 = df[col].quantile(0.25)
    q3 = df[col].quantile(0.75)
    iqr = q3 - q1
    seuil = q3 + 1.5 * iqr
    return df[df[col] > seuil]

bacteries_df, staph_df, tests_df, other_df, pheno_df = load_data()

st.title("Tableau de bord ASTER – Surveillance bactérienne")
bacterie = st.selectbox("Bactéries disponibles", bacteries_df["Category"].unique())

if bacterie != "Staphylococcus aureus":
    st.info("Module disponible uniquement pour Staphylococcus aureus.")
    st.stop()

st.header("Analyse : Staphylococcus aureus")
tab1, tab2, tab3, tab4 = st.tabs([
    "Alertes par service", "Évolution résistance", "Phénotypes", "Alertes par bactérie"
])

with tab1:
    st.subheader("Services avec Vancomycine 'R'")
    alertes = staph_df[staph_df["Vancomycine"] == "R"]
    st.dataframe(alertes[["DATE_ENTREE", "LIBELLE_DEMANDEUR", "Vancomycine"]])

with tab2:
    st.subheader("Évolution des résistances par antibiotique")
    ab_option = st.selectbox("Choisir un antibiotique :", [
        "Vancomycin", "Teicoplanin", "Gentamicin", "Oxacillin",
        "Daptomycin", "Clindamycin", "SXT", "Linezolid"
    ])

    if ab_option in ["Vancomycin", "Teicoplanin", "Gentamicin", "Oxacillin"]:
        df = tests_df
        x_col = "Semaine"
    else:
        df = other_df
        x_col = "Week"

    # Recherche flexible de colonne
    col_options = [
        f"% R {ab_option}",
        f"%{ab_option}",
        f"%R {ab_option}"
    ]
    y_col = next((col for col in col_options if col in df.columns), None)

    if y_col is None:
        st.error(f"Aucune donnée disponible pour {ab_option}")
        st.stop()

    fig = px.line(df, x=x_col, y=y_col, title=f"% Résistance à {ab_option}")
    outliers = detect_outliers(df, y_col)
    fig.add_scatter(x=outliers[x_col], y=outliers[y_col], mode='markers',
                    marker=dict(color='red', size=10), name="Alerte")
    st.plotly_chart(fig)

with tab3:
    st.subheader("Phénotypes (alerte si VRSA ≥ 1)")
    if not pheno_df.empty and "week" in pheno_df.columns:
        pheno_df["week"] = pd.to_datetime(pheno_df["week"], errors="coerce")
        pheno_df = pheno_df.dropna(subset=["week"])
        pheno_melted = pheno_df.melt(id_vars="week", var_name="Phénotype", value_name="N")

        fig = px.line(pheno_melted, x="week", y="N", color="Phénotype", title="Évolution des phénotypes")

        if "VRSA" in pheno_df.columns:
            alerts = pheno_df[pheno_df["VRSA"] >= 1]
            fig.add_scatter(x=alerts["week"], y=alerts["VRSA"], mode="markers",
                            marker=dict(color="red", size=10), name="VRSA Alerte")
        st.plotly_chart(fig)
    else:
        st.warning("Fichier de phénotypes vide ou mal formé.")

with tab4:
    st.subheader("Alerte par bactérie – Accès dynamique")

    for esp in bacteries_df["Category"].unique():
        col1, col2 = st.columns([4, 1])
        with col1:
            st.write(esp)
        with col2:
            if st.button(f"Voir alertes", key=esp):
                if esp == "Staphylococcus aureus":
                    data = staph_df[staph_df["Vancomycine"] == "R"]
                    st.write(f"📊 Alertes pour **{esp}** :")
                    st.dataframe(data)
                else:
                    st.info(f"Aucune donnée détaillée pour {esp} encore.")
