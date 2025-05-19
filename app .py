
# app.py

import streamlit as st
import pandas as pd
import plotly.express as px

# Chargement des fichiers
@st.cache_data
def load_data():
    bacteries_df = pd.read_excel("TOUS les bacteries a etudier.xlsx")
    staph_weekly_df = pd.read_excel("staph aureus hebdomadaire excel.xlsx")
    tests_df = pd.read_csv("tests_par_semaine_antibiotiques_2024.csv")
    other_ab_df = pd.read_excel("other Antibiotiques staph aureus.xlsx")
    pheno_df = pd.read_excel("staph_aureus_pheno_final.xlsx")
    return bacteries_df, staph_weekly_df, tests_df, other_ab_df, pheno_df

bacteries_df, staph_weekly_df, tests_df, other_ab_df, pheno_df = load_data()

# PAGE D'ACCUEIL
st.title("🔬 Tableau de Bord ASTER – Surveillance Bactérienne")
st.subheader("Choisissez une bactérie à explorer :")

bacterie_selectionnee = st.selectbox("Bactéries disponibles", bacteries_df["Category"].unique())

if bacterie_selectionnee == "Staphylococcus aureus":
    st.switch_page("staph_aureus.py")
