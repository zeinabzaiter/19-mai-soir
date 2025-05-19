import streamlit as st
import pandas as pd
import plotly.express as px

# ====== FONCTIONS ======
@st.cache_data
def load_data():
    bacteries_df = pd.read_excel("TOUS_les_bacteries_a_etudier.xlsx")
    staph_weekly_df = pd.read_excel("staph_aureus_hebdomadaire.xlsx")
    tests_df = pd.read_csv("tests_par_semaine_antibiotiques_2024.csv")
    other_ab_df = pd.read_excel("other_Antibiotiques_staph_aureus.xlsx")
    pheno_df = pd.read_excel("staph_aureus_pheno_final.xlsx")
    return bacteries_df, staph_weekly_df, tests_df, other_ab_df, pheno_df

def detect_tukey_outliers(df, col):
    q1 = df[col].quantile(0.25)
    q3 = df[col].quantile(0.75)
    iqr = q3 - q1
    seuil = q3 + 1.5 * iqr
    return df[df[col] > seuil]

# ====== CHARGEMENT DES DONNEES ======
bacteries_df, staph_weekly_df, tests_df, other_ab_df, pheno_df = load_data()

# ====== PAGE D'ACCUEIL ======
st.set_page_config(page_title="Dashboard ASTER", layout="wide")
st.title("Tableau de bord ASTER – Surveillance bactérienne")
st.markdown("Choisissez une bactérie à explorer :")

bacterie = st.selectbox("Bactéries disponibles", bacteries_df["Category"].unique())

if bacterie != "Staphylococcus aureus":
    st.info("Module uniquement disponible pour Staphylococcus aureus dans cette version.")
    st.stop()

# ====== MODULE STAPHYLOCOCCUS AUREUS ======
st.header("Analyse : Staphylococcus aureus")

tab1, tab2, tab3 = st.tabs(["Alertes par service", "Evolution résistance", "Phenotypes"])

# Onglet 1 : Alertes par service
with tab1:
    st.subheader("Services avec au moins 1 souche résistante à la Vancomycine")
    vanco_alerts = staph_weekly_df[staph_weekly_df["Vancomycine"] == "R"]
    st.dataframe(vanco_alerts[["DATE_ENTREE", "LIBELLE_DEMANDEUR", "Vancomycine"]])

# Onglet 2 : Evolution des résistances
with tab2:
    st.subheader("Evolution des résistances (avec détection par la règle de Tukey)")
    ab_option = st.selectbox("Choisir un antibiotique :", [
        "Vancomycin", "Teicoplanin", "Gentamicin", "Oxacillin", 
        "Daptomycin", "Clindamycin", "SXT", "Linezolid"
    ])

    if ab_option in tests_df.columns:
        df = tests_df
        y_col = f"% R {ab_option}"
        fig = px.line(df, x="Semaine", y=y_col, title=f"% Résistance à {ab_option}")
        outliers = detect_tukey_outliers(df, y_col)
        fig.add_scatter(x=outliers["Semaine"], y=outliers[y_col], mode='markers',
                        marker=dict(color='red', size=10), name="Alerte")
        st.plotly_chart(fig)

    elif ab_option in other_ab_df.columns:
        df = other_ab_df
        y_col = f"% R {ab_option}"
        fig = px.line(df, x="Week", y=y_col, title=f"% Résistance à {ab_option}")
        outliers = detect_tukey_outliers(df, y_col)
        fig.add_scatter(x=outliers["Week"], y=outliers[y_col], mode='markers',
                        marker=dict(color='red', size=10), name="Alerte")
        st.plotly_chart(fig)

    else:
        st.warning("Aucune donnée trouvée pour cet antibiotique.")

# Onglet 3 : Phénotypes
with tab3:
    st.subheader("Evolution des phénotypes avec détection VRSA")
    pheno_df["week"] = pd.to_datetime(pheno_df["week"])
    pheno_long = pheno_df.melt(id_vars="week", var_name="Phenotype", value_name="N")

    fig = px.line(pheno_long, x="week", y="N", color="Phenotype", title="Distribution des phénotypes")
    vrsa_alerts = pheno_df[pheno_df["VRSA"] >= 1]
    fig.add_scatter(x=vrsa_alerts["week"], y=vrsa_alerts["VRSA"], mode='markers',
                    marker=dict(color='red', size=10), name="Alerte VRSA")
    st.plotly_chart(fig)
