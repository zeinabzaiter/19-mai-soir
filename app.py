import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

st.set_page_config(page_title="Tableau de bord ASTER", layout="wide")
st.title("Tableau de bord ASTER – Surveillance bactérienne")

# 📁 Chargement des fichiers
@st.cache_data
def load_data():
    try:
        pheno_df = pd.read_excel("staph_aureus_pheno_final.xlsx")
        weekly_df = pd.read_excel("staph aureus hebdomadaire excel.xlsx")
        test_df = pd.read_csv("tests_par_semaine_antibiotiques_2024.csv")
        other_ab_df = pd.read_excel("other Antibiotiques staph aureus.xlsx")
    except Exception as e:
        st.error(f"Erreur de chargement des fichiers : {e}")
        return None, None, None, None

    return pheno_df, weekly_df, test_df, other_ab_df

pheno_df, weekly_df, test_df, other_ab_df = load_data()

if pheno_df is None:
    st.stop()

# 🧼 Nettoyage des données
pheno_df["week"] = pd.to_datetime(pheno_df["week"])
weekly_df["DATE_ENTREE"] = pd.to_datetime(weekly_df["DATE_ENTREE"], errors="coerce")
weekly_df.dropna(subset=["DATE_ENTREE"], inplace=True)

# Ajout colonne semaine dans weekly_df
weekly_df["Semaine"] = weekly_df["DATE_ENTREE"].dt.to_period("W").astype(str)

# 🧪 Fonction Tukey pour alarme
def detect_alarms_tukey(data, column):
    q1 = data[column].quantile(0.25)
    q3 = data[column].quantile(0.75)
    iqr = q3 - q1
    threshold = q3 + 1.5 * iqr
    return data[column] > threshold

# 🔔 Alarme spéciale pour VRSA
pheno_df["Alerte_VRSA"] = pheno_df["VRSA"].apply(lambda x: 1 if x >= 1 else 0)

# 🔔 Alarmes pour autres phénotypes (Tukey)
for col in ["MRSA", "Other", "Wild"]:
    if col in pheno_df.columns:
        pheno_df[f"Alerte_{col}"] = detect_alarms_tukey(pheno_df, col)

# 📌 Bactéries disponibles (liste simulée ici)
bacteries = ["Staphylococcus aureus"]  # car tous les fichiers concernent cette espèce
selected_bacteria = st.selectbox("🧫 Bactéries disponibles", bacteries)
# --- Onglets ---
tab1, tab2, tab3 = st.tabs(["Alertes par service", "Évolution résistance", "Phénotypes"])

with tab2:
    st.header("Évolution des résistances par antibiotique")

    if test_df is not None:
        ab_list = test_df.columns.tolist()
        ab_list.remove("Semaine") if "Semaine" in ab_list else None
        ab_option = st.selectbox("Choisir un antibiotique :", ab_list)

        try:
            df = test_df[["Semaine", ab_option]].dropna()
            fig = px.line(
                df,
                x="Semaine",
                y=ab_option,
                title=f"% Résistance à {ab_option}",
                markers=True,
                template="simple_white"
            )

            # Calcul seuil (méthode Tukey) et affichage en rouge si dépassement
            seuil = df[ab_option].quantile(0.75) + 1.5 * (df[ab_option].quantile(0.75) - df[ab_option].quantile(0.25))
            fig.add_hline(y=seuil, line_dash="dash", line_color="red", annotation_text="Seuil d’alerte (Tukey)", annotation_position="top right")

            # Mettre en rouge les points qui dépassent
            df["Alerte"] = df[ab_option] > seuil
            fig.update_traces(marker=dict(color=df["Alerte"].map({True: 'red', False: 'blue'})))

            st.plotly_chart(fig, use_container_width=True)
        except Exception as e:
            st.error(f"Aucune donnée disponible pour {ab_option} ou erreur : {e}")
with tab3:
    st.header("Phénotypes (alerte si VRSA ≥ 1)")

    if pheno_df is not None and not pheno_df.empty:
        try:
            st.subheader("Vue générale des phénotypes")
            df_show = pheno_df[["week", "VRSA", "MRSA", "Other", "Wild", "Alerte_VRSA"]]
            st.dataframe(df_show)

            st.subheader("Courbe de suivi VRSA")
            fig = px.line(
                df_show,
                x="week",
                y="VRSA",
                title="Cas de VRSA par semaine",
                markers=True
            )
            fig.update_traces(marker=dict(color=df_show["Alerte_VRSA"].map({1: 'red', 0: 'blue'})))
            st.plotly_chart(fig, use_container_width=True)

            st.info("🔴 Points rouges = semaines avec au moins un cas VRSA")
        except Exception as e:
            st.error(f"Erreur dans la section phénotypes : {e}")
    else:
        st.warning("Aucune donnée de phénotypes chargée.")
