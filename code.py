import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from PIL import Image
from fpdf import FPDF
import tempfile
import os
from pathlib import Path

# =========================
# CONFIGURATION DE LA PAGE
# =========================
st.set_page_config(
    page_title="Container Dashboard",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# =========================
# CONSTANTES
# =========================
CAPACITY_MAP = {"20GP": 33, "40GP": 67, "40HQ": 76}
FILL_RATE_THRESHOLD = 70
MAX_ROWS_PER_PAGE = 8

# =========================
# FONCTIONS UTILITAIRES
# =========================
@st.cache_data
def load_excel(file):
    """Charge et nettoie le fichier Excel"""
    df = pd.read_excel(file)
    df.columns = df.columns.str.strip()
    return df

def calculate_summary(df, cbm_col):
    """Calcule le résumé du remplissage des conteneurs"""
    summary = df.groupby(
        ["CONTAINER NO", "CTNER.SIZE"], as_index=False
    ).agg({cbm_col: "sum"})
    
    summary.rename(columns={cbm_col: "TOTAL_VOLUME"}, inplace=True)
    summary["CAPACITY"] = summary["CTNER.SIZE"].map(CAPACITY_MAP)
    summary["FILL_RATE_%"] = (summary["TOTAL_VOLUME"] * 100 / summary["CAPACITY"]).round(2)
    summary["STATUS"] = summary["FILL_RATE_%"].apply(
        lambda x: "✅ OK" if x >= FILL_RATE_THRESHOLD else "❌ NON CONFORME"
    )
    summary["STATUS_COLOR"] = summary["FILL_RATE_%"].apply(
        lambda x: "green" if x >= FILL_RATE_THRESHOLD else "red"
    )
    
    return summary

def create_chart(data, container_col, fill_rate_col, threshold=FILL_RATE_THRESHOLD):
    """Crée le graphique du taux de remplissage"""
    fig, ax = plt.subplots(figsize=(10, 5))
    
    bars = ax.bar(data[container_col], data[fill_rate_col], 
                  color=['#2ecc71' if x >= threshold else '#e74c3c' 
                         for x in data[fill_rate_col]], 
                  alpha=0.8, edgecolor='black', linewidth=1)
    
    ax.axhline(y=threshold, color='red', linestyle='--', 
               linewidth=2, label=f'Seuil ({threshold}%)', zorder=5)
    
    ax.set_ylim(0, 100)
    ax.set_title("Taux de Remplissage par Conteneur", fontsize=14, fontweight='bold')
    ax.set_ylabel("Taux de remplissage (%)", fontsize=11)
    ax.set_xlabel("Numéro du conteneur", fontsize=11)
    ax.grid(True, alpha=0.3, axis='y')
    ax.legend(loc='upper right')
    
    # Ajout des valeurs sur les barres
    for bar in bars:
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height + 1,
                f'{height:.1f}%', ha='center', va='bottom', fontsize=9)
    
    fig.tight_layout()
    return fig

def display_metrics(summary):
    """Affiche les métriques principales"""
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Nombre total de conteneurs", len(summary))
    with col2:
        avg_fill = summary["FILL_RATE_%"].mean()
        st.metric("Taux de remplissage moyen", f"{avg_fill:.1f}%")
    with col3:
        compliant = len(summary[summary["FILL_RATE_%"] >= FILL_RATE_THRESHOLD])
        st.metric("Conteneurs conformes", f"{compliant}/{len(summary)}")
    with col4:
        total_volume = summary["TOTAL_VOLUME"].sum()
        total_capacity = summary["CAPACITY"].sum()
        st.metric("Volume total", f"{total_volume:.1f} / {total_capacity:.0f} m³")

def create_pdf(summary, full_title, chart_path, model, bl_no):
    """Génère le rapport PDF"""
    pdf = FPDF("P", "mm", "A4")
    pdf.add_page()
    
    # Entête
    logo_path = "entete.PNG"
    if os.path.exists(logo_path):
        pdf.image(logo_path, x=0, y=0, w=210, h=25)
        pdf.ln(55)
    else:
        pdf.ln(20)
    
    # Titre
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, full_title, ln=True, align="C")
    pdf.ln(5)
    
    # Tableau
    pdf.set_font("Arial", "B", 8)
    page_width = pdf.w - 20
    col_width = page_width / 6
    
    headers = ["CONTAINER NO", "SIZE", "TOTAL VOLUME", "CAPACITY", "FILL RATE", "STATUS"]
    
    for header in headers:
        pdf.cell(col_width, 8, header, border=1, align="C")
    pdf.ln()
    
    pdf.set_font("Arial", "", 8)
    
    for i, (_, row) in enumerate(summary.iterrows()):
        if i >= MAX_ROWS_PER_PAGE:
            pdf.add_page()
            # Re-titre du tableau sur nouvelle page
            for header in headers:
                pdf.cell(col_width, 8, header, border=1, align="C")
            pdf.ln()
        
        row_values = [
            row["CONTAINER NO"],
            row["CTNER.SIZE"],
            f"{row['TOTAL_VOLUME']:.2f}",
            f"{row['CAPACITY']:.0f}",
            f"{row['FILL_RATE_%']:.1f}%",
            row["STATUS"]
        ]
        
        for j, value in enumerate(row_values):
            if j == 5:  # Colonne STATUS
                pdf.set_text_color(0, 150, 0) if "OK" in value else pdf.set_text_color(255, 0, 0)
            else:
                pdf.set_text_color(0, 0, 0)
            
            pdf.cell(col_width, 8, str(value), border=1, align="C")
        pdf.ln()
    
    # Graphique
    pdf.ln(5)
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 10, "Visualisation du taux de remplissage", ln=True, align="C")
    pdf.ln(3)
    pdf.image(chart_path, x=10, w=190)
    
    return pdf.output(dest="S").encode("latin1")

# =========================
# AFFICHAGE DES LOGOS
# =========================
def display_header():
    """Affiche l'en-tête avec les logos"""
    try:
        container_logo = Image.open("conteneur_logo.png")
        stream_logo = Image.open("stream_logo.png")
        
        col1, col2, col3 = st.columns([1, 5, 1])
        
        with col1:
            st.image(container_logo, width=150)
        with col2:
            st.title("📦 Container Filling Industrial Dashboard")
            st.caption("Supply Chain Analysis - BOM & Packing Control")
        with col3:
            st.image(stream_logo, width=150)
    except FileNotFoundError:
        st.title("📦 Container Filling Industrial Dashboard")
        st.caption("Supply Chain Analysis - BOM & Packing Control")

# =========================
# GUIDE UTILISATEUR
# =========================
def display_user_guide():
    """Affiche le guide utilisateur"""
    with st.expander("📘 Manuel d'utilisation / User Guide"):
        st.markdown("""
        ### 📋 Instructions d'utilisation
        
        1. **Informations d'étude** : Remplissez les informations de base
        2. **Import du fichier** : Uploadez votre fichier Excel contenant les données des conteneurs
        3. **Analyse automatique** : Le dashboard calcule automatiquement :
           - Le volume total par conteneur
           - Le taux de remplissage
           - La conformité (OK si ≥70%)
        
        ### 📊 Format du fichier Excel attendu
        - Colonnes requises : `CONTAINER NO`, `CTNER.SIZE`, `[CBM]`
        - Le fichier doit contenir une colonne avec "CBM" dans son nom
        - Formats de conteneurs supportés : 20GP, 40GP, 40HQ
        """)

# =========================
# APPLICATION PRINCIPALE
# =========================
def main():
    """Fonction principale de l'application"""
    
    # En-tête
    display_header()
    
    # Guide utilisateur
    display_user_guide()
    
    # Formulaire d'informations
    with st.container():
        st.markdown("### 📦 Study Information")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            packing_type = st.selectbox(
                "Type of Packing List",
                ["Panel", "SP", "SP/MainBoard", "OC"],
                help="Sélectionnez le type de liste de colisage"
            )
        
        with col2:
            model = st.text_input("Model", placeholder="Entrez le modèle...")
        
        with col3:
            bl_no = st.text_input("BL No", placeholder="Numéro de connaissement...")
    
    st.markdown("---")
    
    # Titre dynamique
    if model and bl_no:
        full_title = f"Container Filling Industrial Dashboard of {packing_type} of {model}__{bl_no}"
    else:
        full_title = "Container Filling Industrial Dashboard"
    
    st.subheader(full_title)
    
    # Upload du fichier
    file = st.file_uploader(
        "📂 Upload Excel File", 
        type=["xlsx"],
        help="Format attendu : Excel avec colonnes CONTAINER NO, CTNER.SIZE, et une colonne contenant 'CBM'"
    )
    
    if file is not None:
        try:
            # Chargement des données
            with st.spinner("Chargement et analyse des données..."):
                df = load_excel(file)
            
            # Aperçu des données
            with st.expander("🔍 Aperçu des données brutes"):
                st.dataframe(df, use_container_width=True)
            
            # Recherche de la colonne CBM
            cbm_col = next((col for col in df.columns if "CBM" in col.upper()), None)
            
            if cbm_col:
                # Calcul du résumé
                summary = calculate_summary(df, cbm_col)
                
                # Métriques
                display_metrics(summary)
                
                # Affichage du tableau des résultats
                st.markdown("---")
                st.subheader("📊 Résultats par conteneur")
                
                # Formatage stylisé du tableau
                styled_summary = summary.style.apply(
                    lambda x: ['background-color: #90EE90' if v == '✅ OK' 
                               else 'background-color: #FFB6C1' for v in x], 
                    subset=['STATUS']
                )
                st.dataframe(styled_summary, use_container_width=True)
                
                # Graphique
                st.subheader("📈 Taux de remplissage")
                fig = create_chart(summary, "CONTAINER NO", "FILL_RATE_%")
                st.pyplot(fig)
                plt.close(fig)
                
                # Génération du PDF
                st.markdown("---")
                st.subheader("📄 Export du rapport")
                
                # Sauvegarde temporaire du graphique pour le PDF
                with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp_img:
                    fig_pdf = create_chart(summary, "CONTAINER NO", "FILL_RATE_%")
                    fig_pdf.savefig(tmp_img.name, dpi=300, bbox_inches="tight")
                    plt.close(fig_pdf)
                    
                    # Création du PDF
                    pdf_bytes = create_pdf(summary, full_title, tmp_img.name, model, bl_no)
                    
                    # Nettoyage
                    os.unlink(tmp_img.name)
                
                # Bouton de téléchargement
                st.download_button(
                    label="📥 Télécharger le rapport PDF",
                    data=pdf_bytes,
                    file_name=f"{model}_{bl_no}_dashboard.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )
                
            else:
                st.error("❌ Colonne 'CBM' introuvable. Vérifiez que votre fichier contient une colonne avec 'CBM' dans son nom.")
        
        except Exception as e:
            st.error(f"❌ Erreur lors du traitement du fichier : {str(e)}")
            st.info("Vérifiez le format de votre fichier Excel (colonnes requises : CONTAINER NO, CTNER.SIZE, [CBM])")

if __name__ == "__main__":
    main()
