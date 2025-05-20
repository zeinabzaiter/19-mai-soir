import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import os

st.set_page_config(page_title="Tableau de bord ASTER", layout="wide")
st.title("🦠 Tableau de bord ASTER – Surveillance bactérienne")

# Fonction utilitaire pour charger un fichier
def charger_fichier_excel(nom_fichier, colonnes_obligatoires=None, feuille=0):
    try:
        df = pd.read_excel(nom_fichier, sheet_name=feuille)
        if colonnes_obligatoires:
            for col in colonnes_obligatoires:
                if col not in df.columns:
                    st.warning(f"Colonne obligatoire '{col}' non trouvée dans {nom_fichier}")
        return df
    except FileNotFoundError:
        st.error(f"❌ Fichier introuvable : {nom_fichier}")
        return pd.DataFrame()
    except Exception as e:
        st.error(f"❌ Erreur de chargement {nom_fichier} : {e}")
        return pd.DataFrame()

# Fonction de nettoyage du nom de colonnes
def nettoyer_colonnes(df):
    df.columns = df.columns.str.strip()
    return df

# Chargement des fichiers avec noms exacts
df_bacteries = charger_fichier_excel("TOUS_les_bacteries_a_etudier.xlsx", colonnes_obligatoires=["Espèce"])
df_pheno = charger_fichier_excel("staph_aureus_pheno_final.xlsx")
df_autres_ab = charger_fichier_excel("other_Antibiotiques_staph_aureus.xlsx")
df_tests = pd.read_csv("tests_par_semaine_antibiotiques_2024.csv", sep=',')
df_hebdo = charger_fichier_excel("staph_aureus_hebdomadaire.xlsx")

# Nettoyage
df_bacteries = nettoyer_colonnes(df_bacteries)
df_pheno = nettoyer_colonnes(df_pheno)
df_autres_ab = nettoyer_colonnes(df_autres_ab)
df_tests = nettoyer_colonnes(df_tests)
df_hebdo = nettoyer_colonnes(df_hebdo)
# Vérification colonne 'Espèce'
if "Espèce" not in df_bacteries.columns:
    st.error("Colonne 'Espèce' non trouvée dans le fichier des bactéries.")
    st.stop()

# Menu déroulant
selected_bacteria = st.selectbox("🌿 Bactéries disponibles", df_bacteries["Espèce"].unique())

# Affichage spécial pour Staphylococcus aureus
if selected_bacteria == "Staphylococcus aureus":
    with st.expander("📋 Détails sur Staphylococcus aureus", expanded=True):
        st.subheader("Analyse spécifique : Staphylococcus aureus")
        st.write("Résumé des données hebdomadaires :")
        if not df_hebdo.empty:
            st.dataframe(df_hebdo)
        else:
            st.warning("Aucune donnée hebdomadaire chargée pour Staphylococcus aureus.")

# Organisation par onglets
tabs = st.tabs(["Alertes par service", "Évolution résistance", "Phénotypes"])

# -------- Onglet 1 : Alertes par service --------
with tabs[0]:
    st.subheader("Alertes par service")
    if not df_tests.empty:
        if "Libellé demandeur" in df_tests.columns:
            alerts = df_tests.groupby("Libellé demandeur").size().reset_index(name="Nbre de tests")
            st.bar_chart(alerts.set_index("Libellé demandeur"))
        else:
            st.warning("Colonne 'Libellé demandeur' manquante dans les données de tests.")
    else:
        st.warning("Aucune donnée de tests chargée.")
import plotly.express as px

# -------- Onglet 2 : Évolution résistance --------
with tabs[1]:
    st.subheader("Évolution des résistances par antibiotique")

    if not df_tests.empty:
        ab_list = list(df_tests.columns)
        ab_list = [col for col in ab_list if col not in ["Semaine", "Espèce", "Libellé demandeur"]]

        ab_option = st.selectbox("Choisir un antibiotique :", ab_list)

        try:
            df = df_tests[["Semaine", ab_option]].dropna()

            # 🔴 Règle spéciale pour VRSA/Vancomycine
            if ab_option.lower() in ["vrsa", "vancomycine"]:
                df["Alerte"] = df[ab_option].apply(lambda x: 1 if x >= 1 else 0)
            else:
                q1 = df[ab_option].quantile(0.25)
                q3 = df[ab_option].quantile(0.75)
                iqr = q3 - q1
                seuil = q3 + 1.5 * iqr
                df["Alerte"] = df[ab_option].apply(lambda x: 1 if x > seuil else 0)

            fig = px.line(df, x="Semaine", y=ab_option, markers=True)
            alertes = df[df["Alerte"] == 1]
            fig.add_scatter(x=alertes["Semaine"], y=alertes[ab_option], mode='markers',
                            marker=dict(color='red', size=10), name="Alarme")

            st.plotly_chart(fig)

        except KeyError:
            st.error(f"Aucune donnée disponible pour {ab_option}")
    else:
        st.warning("Aucune donnée de tests chargée.")


# -------- Onglet 3 : Phénotypes --------
with tabs[2]:
    st.subheader("Phénotypes (alerte si VRSA ≥ 1)")

    if not df_pheno.empty:
        if selected_bacteria in df_pheno.columns:
            value = df_pheno[selected_bacteria].sum()
            st.metric(label="Nombre de cas VRSA", value=int(value))
            if value >= 1:
                st.error("⚠️ Alerte déclenchée : au moins 1 cas de VRSA détecté.")
            else:
                st.success("✅ Aucun cas de VRSA détecté.")
        else:
            st.warning(f"Aucune donnée de phénotype pour {selected_bacteria}.")
    else:
        st.warning("Aucune donnée de phénotypes chargée.")
