import streamlit as st
import pandas as pd
import plotly.express as px

# Chargement des fichiers
@st.cache_data
def load_data():
    try:
        bact_df = pd.read_excel("TOUS_les_bacteries_a_etudier.xlsx")
        bact_df.rename(columns={"Category": "Espèce"}, inplace=True)
    except Exception as e:
        st.error(f"Erreur de chargement des bactéries : {e}")
        bact_df = pd.DataFrame()

    try:
        tests_df = pd.read_csv("tests_par_semaine_antibiotiques_2024.csv")
    except Exception as e:
        st.error(f"Erreur de chargement des tests hebdomadaires : {e}")
        tests_df = pd.DataFrame()

    try:
        other_df = pd.read_excel("other Antibiotiques staph aureus.xlsx")
    except Exception as e:
        st.error(f"Erreur de chargement des autres antibiotiques : {e}")
        other_df = pd.DataFrame()

    return bact_df, tests_df, other_df

# Initialisation des données
bacteries_df, tests_df, other_df = load_data()

st.title("Tableau de bord ASTER – Surveillance bactérienne")

if bacteries_df.empty:
    st.warning("Le fichier des bactéries est vide ou non chargé.")
    st.stop()

# Sélection de la bactérie
try:
    selected_bacterium = st.selectbox("🦠 Bactéries disponibles", bacteries_df["Espèce"].unique())
except KeyError:
    st.error("Colonne 'Espèce' introuvable dans le fichier.")
    st.stop()

# Création des onglets
tabs = st.tabs(["Alertes par service", "Évolution résistance", "Phénotypes"])

# Onglet 1 : Alertes par service
with tabs[0]:
    st.subheader("Alertes par service (basé sur règle de Tukey sauf VRSA/Vancomycine)")

    if not tests_df.empty:
        alertes = []

        for ab in tests_df.columns[2:]:
            if ab.lower() in ["vrsa", "vancomycine"]:
                alertes.append((ab, tests_df[ab].sum()))
            else:
                q1 = tests_df[ab].quantile(0.25)
                q3 = tests_df[ab].quantile(0.75)
                iqr = q3 - q1
                seuil = q3 + 1.5 * iqr
                alertes.append((ab, (tests_df[ab] > seuil).sum()))

        alertes_df = pd.DataFrame(alertes, columns=["Antibiotique", "Nombre d'alertes"])
        st.dataframe(alertes_df)
    else:
        st.warning("Aucune donnée de tests hebdomadaires disponible.")

# Onglet 2 : Évolution résistance
with tabs[1]:
    st.subheader("Évolution des résistances par antibiotique")

    if not tests_df.empty:
        antibiotics = [col for col in tests_df.columns if col not in ["Semaine", "Espèce"]]
        ab_option = st.selectbox("Choisir un antibiotique :", antibiotics)

        if ab_option in tests_df.columns:
            fig = px.line(tests_df, x="Semaine", y=ab_option,
                          title=f"% Résistance à {ab_option}")
            st.plotly_chart(fig)
        else:
            st.error(f"Aucune donnée disponible pour {ab_option}.")
    else:
        st.warning("Aucune donnée de tests disponible.")

# Onglet 3 : Phénotypes
with tabs[2]:
    st.subheader("Phénotypes (alerte si VRSA ≥ 1)")

    if not other_df.empty:
        ab_cols = [col for col in other_df.columns if col != "Semaine"]
        ab_option = st.selectbox("Choisir un antibiotique pour le phénotype :", ab_cols)

        if ab_option in other_df.columns:
            try:
                df = other_df[["Semaine", ab_option]].dropna()
                fig = px.bar(df, x="Semaine", y=ab_option, title=f"Phénotype - {ab_option}")
                st.plotly_chart(fig)
            except KeyError:
                st.error("Colonnes manquantes pour les phénotypes.")
        else:
            st.warning("Antibiotique non trouvé dans les données de phénotypes.")
    else:
        st.warning("Aucune donnée de phénotypes chargée.")
