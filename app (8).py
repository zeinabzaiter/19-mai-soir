import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

st.set_page_config(page_title="Tableau de bord ASTER", layout="wide")

# Fonction pour charger les fichiers
def charger_fichier_excel(nom_fichier):
    try:
        return pd.read_excel(nom_fichier)
    except FileNotFoundError:
        st.error(f"Erreur de chargement du fichier : {nom_fichier}")
        return pd.DataFrame()

def charger_fichier_csv(nom_fichier):
    try:
        return pd.read_csv(nom_fichier)
    except FileNotFoundError:
        st.error(f"Erreur de chargement du fichier : {nom_fichier}")
        return pd.DataFrame()

# Chargement des fichiers
df_bacteries = charger_fichier_excel("TOUS_les_bacteries_a_etudier.xlsx")
df_pheno = charger_fichier_excel("staph_aureus_pheno_final.xlsx")
df_tests = charger_fichier_csv("tests_par_semaine_antibiotiques_2024.csv")
df_autres_ab = charger_fichier_excel("other Antibiotiques staph aureus.xlsx")
df_staph_service = charger_fichier_excel("staph_aureus_hebdomadaire.xlsx")

# Interface utilisateur
st.title("🦠 Tableau de bord ASTER – Surveillance bactérienne")

if df_bacteries.empty or "Espèce" not in df_bacteries.columns:
    st.error("Colonne 'Espèce' introuvable dans le fichier TOUS_les_bacteries_a_etudier.xlsx.")
    st.stop()

selected_bacterie = st.selectbox("🌿 Bactéries disponibles", df_bacteries["Espèce"].unique())

# Affichage par onglets
onglet = st.tabs(["Alertes par service", "Évolution résistance", "Phénotypes"])

# Onglet Alertes par service
with onglet[0]:
    st.subheader("Alertes par service")
    if not df_staph_service.empty:
        if {"Libellé Demandeur", "Alerte"}.issubset(df_staph_service.columns):
            alertes_par_service = df_staph_service.groupby("Libellé Demandeur")["Alerte"].sum().reset_index()
            fig = px.bar(alertes_par_service, x="Libellé Demandeur", y="Alerte", title="Alertes par service")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("Colonnes attendues non présentes dans les données.")
    else:
        st.warning("Données hebdomadaires Staph Aureus non chargées.")

# Onglet Évolution résistance
with onglet[1]:
    st.subheader("Évolution des résistances par antibiotique")

    if not df_tests.empty:
        ab_list = list(df_tests.columns)
        if "Semaine" in ab_list:
            ab_list.remove("Semaine")

        ab_option = st.selectbox("Choisir un antibiotique :", ab_list)
        if ab_option:
            df = df_tests[["Semaine", ab_option]].dropna()
            q1 = df[ab_option].quantile(0.25)
            q3 = df[ab_option].quantile(0.75)
            seuil = q3 + 1.5 * (q3 - q1)
            if ab_option in ["VANCO", "VRSA"]:
                df["Alerte"] = df[ab_option].apply(lambda x: 1 if x >= 1 else 0)
            else:
                df["Alerte"] = df[ab_option].apply(lambda x: 1 if x > seuil else 0)
            fig = px.line(df, x="Semaine", y=ab_option, markers=True, title=f"Évolution de la résistance - {ab_option}")
            fig.add_scatter(x=df[df["Alerte"] == 1]["Semaine"], y=df[df["Alerte"] == 1][ab_option],
                            mode="markers", marker=dict(color="red", size=10), name="Alerte")
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("Données de tests par semaine non disponibles.")

# Onglet Phénotypes
with onglet[2]:
    st.subheader("Phénotypes (alerte si VRSA ≥ 1)")
    if selected_bacterie == "Staphylococcus aureus":
        if not df_pheno.empty:
            seuils = df_pheno.drop(columns=["Phénotype"]).mean() + 1.5 * (df_pheno.drop(columns=["Phénotype"]).quantile(0.75) - df_pheno.drop(columns=["Phénotype"]).quantile(0.25))
            alertes = pd.DataFrame({
                "Phénotype": df_pheno["Phénotype"],
                "Valeur": df_pheno.drop(columns=["Phénotype"]).mean(axis=1),
                "Alerte": df_pheno["VRSA"].apply(lambda x: 1 if x >= 1 else 0)
            })
            st.dataframe(alertes)
        else:
            st.warning("Aucune donnée de phénotypes chargée.")
    else:
        st.info("Pas de données de phénotypes pour cette bactérie.")