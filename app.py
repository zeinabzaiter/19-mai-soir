import streamlit as st
import pandas as pd
import plotly.express as px

# ----------- FONCTIONS -----------

@st.cache_data
def load_data():
    bacteria_df = pd.read_excel("TOUS_les_bacteries_a_etudier.xlsx")
    staph_df = pd.read_excel("staph_aureus_hebdomadaire.xlsx")
    tests_df = pd.read_csv("tests_par_semaine_antibiotiques_2024.csv")
    other_ab_df = pd.read_excel("other_Antibiotiques_staph_aureus.xlsx")
    pheno_df = pd.read_excel("staph_aureus_pheno_final.xlsx")
    return bacteria_df, staph_df, tests_df, other_ab_df, pheno_df

def detect_alarms(df, col):
    if "Vancomycin" in col or "VRSA" in col:
        return df[df[col] > 0], "≥ 1 cas"
    q1 = df[col].quantile(0.25)
    q3 = df[col].quantile(0.75)
    iqr = q3 - q1
    seuil = q3 + 1.5 * iqr
    return df[df[col] > seuil], f"> {seuil:.2f} (Tukey)"

# ----------- APPLICATION -----------

bacteries_df, staph_weekly_df, tests_df, other_df, pheno_df = load_data()

st.set_page_config(page_title="Tableau ASTER", layout="wide")
st.title("Tableau de bord ASTER – Surveillance bactérienne")

selected_bacteria = st.selectbox("🔬 Bactéries disponibles", bacteries_df["Espece"].unique())

if selected_bacteria == "Staphylococcus aureus":
    st.header("🧫 Analyse : Staphylococcus aureus")
    onglets = st.tabs(["🚨 Alertes par service", "📈 Évolution résistance", "🧪 Phénotypes"])

    with onglets[0]:
        st.subheader("🚨 Alertes détectées par service")
        if "Semaine" in staph_weekly_df.columns:
            st.dataframe(
                staph_weekly_df[["Semaine", "Libelle_Demandeur", "Vancomycine"]],
                use_container_width=True
            )
        else:
            st.warning("Fichier hebdomadaire incomplet.")

    with onglets[1]:
        st.subheader("📊 Évolution des résistances par antibiotique")
        ab_option = st.selectbox("Choisir un antibiotique :", other_df.columns[1:])
        if ab_option in other_df.columns:
            df = other_df[["Semaine", ab_option]].dropna()
            y_col = ab_option
            alarms_df, rule = detect_alarms(df, y_col)

            fig = px.line(df, x="Semaine", y=y_col, title=f"% Résistance à {ab_option} ({rule})")
            fig.add_scatter(
                x=alarms_df["Semaine"],
                y=alarms_df[y_col],
                mode='markers',
                marker=dict(size=10, color='red'),
                name="Alerte"
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Aucune donnée disponible.")

    with onglets[2]:
        st.subheader("🧪 Phénotypes (alerte si VRSA ≥ 1)")
        if not pheno_df.empty and "VRSA" in pheno_df.columns:
            vrsa_alerts = pheno_df[pheno_df["VRSA"] > 0]
            if not vrsa_alerts.empty:
                st.dataframe(vrsa_alerts, use_container_width=True)
            else:
                st.success("Aucune alerte VRSA détectée.")
        else:
            st.warning("Données phénotypiques absentes ou colonne 'VRSA' manquante.")
