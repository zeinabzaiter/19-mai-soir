import streamlit as st
import pandas as pd
import plotly.express as px

# ------------------ FONCTIONS ------------------

@st.cache_data
def load_data():
    df_bacteria = pd.read_excel("TOUS_les_bacteries_a_etudier.xlsx")
    df_weekly = pd.read_excel("staph_aureus_hebdomadaire.xlsx")
    df_tests = pd.read_csv("tests_par_semaine_antibiotiques_2024.csv")
    df_other_ab = pd.read_excel("other_Antibiotiques_staph_aureus.xlsx")
    df_pheno = pd.read_excel("staph_aureus_pheno_final.xlsx")
    return df_bacteria, df_weekly, df_tests, df_other_ab, df_pheno

def detect_alerts_tukey(df, col):
    q1 = df[col].quantile(0.25)
    q3 = df[col].quantile(0.75)
    iqr = q3 - q1
    threshold = q3 + 1.5 * iqr
    return df[col] > threshold

def render_alerts_tab(df):
    st.subheader("Alertes par service")
    if "Libelle_Demandeur" in df.columns and "Vancomycine" in df.columns:
        alert_rows = df[df["Vancomycine"] == "R"]
        st.dataframe(alert_rows[["DATE_ENTREE", "Libelle_Demandeur", "Vancomycine"]])
    else:
        st.warning("Colonnes attendues non présentes dans les données.")

def render_evolution_tab(df_weekly, df_tests):
    st.subheader("Évolution des résistances par antibiotique")
    ab_list = list(df_weekly.columns)
    ab_list.remove("Semaine")

    ab_option = st.selectbox("Choisir un antibiotique :", ab_list)

    if ab_option:
        df = df_weekly[["Semaine", ab_option]].dropna()
        fig = px.line(df, x="Semaine", y=ab_option,
                      title=f"% Résistance à {ab_option}")
        
        if ab_option not in ["Vancomycine", "VRSA"]:
            alerts = detect_alerts_tukey(df, ab_option)
            fig.add_scatter(x=df["Semaine"][alerts], y=df[ab_option][alerts],
                            mode="markers", marker=dict(color="red", size=10),
                            name="Alerte")

        st.plotly_chart(fig)

def render_pheno_tab(df_pheno):
    st.subheader("Phénotypes (alerte si VRSA ≥ 1)")

    if df_pheno.empty or "week" not in df_pheno.columns:
        st.warning("Aucune donnée de phénotypes chargée.")
        return

    df = df_pheno.copy()
    df["week"] = pd.to_datetime(df["week"])
    vrsa_cols = [col for col in df.columns if "VRSA" in col]
    alert_weeks = df[df[vrsa_cols].sum(axis=1) >= 1]

    st.dataframe(alert_weeks)

# ------------------ MAIN APP ------------------

st.set_page_config(page_title="Dashboard ASTER", layout="wide")
st.title("Tableau de bord ASTER – Surveillance bactérienne")

try:
    df_bacteria, df_weekly, df_tests, df_other_ab, df_pheno = load_data()
except Exception as e:
    st.error(f"Erreur de chargement des fichiers : {e}")
    st.stop()

# ------------ Sélecteur de bactérie -------------
selected_bacteria = st.selectbox("🦠 Bactéries disponibles", df_bacteria["Espèce"].unique())

# ---------- Pop-up automatique si staph -----------
if selected_bacteria.lower().startswith("staph"):
    with st.expander("🧬 Détails Staphylococcus aureus (cliquez pour voir)", expanded=True):
        summary = df_pheno.describe().transpose()
        st.write("Résumé des phénotypes :")
        st.dataframe(summary)

# ----------------- Onglets ------------------
tabs = st.tabs(["Alertes par service", "Évolution résistance", "Phénotypes"])

with tabs[0]:
    render_alerts_tab(df_bacteria)

with tabs[1]:
    render_evolution_tab(df_weekly, df_tests)

with tabs[2]:
    render_pheno_tab(df_pheno)
