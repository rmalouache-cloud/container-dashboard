import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from PIL import Image
from fpdf import FPDF
import tempfile
import os
from pathlib import Path
import numpy as np

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
    
    return summary

def create_chart(data, container_col, fill_rate_col, threshold=FILL_RATE_THRESHOLD):
    """Crée le graphique du taux de remplissage avec texte diagonal pour les labels"""
    fig, ax = plt.subplots(figsize=(12, 6))
    
    # Création des barres
    bars = ax.bar(range(len(data[container_col])), data[fill_rate_col], 
                  color=['#2ecc71' if x >= threshold else '#e74c3c' 
                         for x in data[fill_rate_col]], 
                  alpha=0.8, edgecolor='black', linewidth=1)
    
    # Ligne de seuil
    ax.axhline(y=threshold, color='red', linestyle='--', 
               linewidth=2, label=f'Seuil ({threshold}%)', zorder=5)
    
    # Configuration des axes
    ax.set_ylim(0, 100)
    ax.set_ylabel("Taux de remplissage (%)", fontsize=12, fontweight='bold')
    ax.set_xlabel("Numéro du conteneur", fontsize=12, fontweight='bold')
    ax.set_title("Taux de Remplissage par Conteneur", fontsize=14, fontweight='bold')
    ax.grid(True, alpha=0.3, axis='y')
    ax.legend(loc='upper right', fontsize=10)
    
    # Rotation des labels pour meilleure lisibilité
    ax.set_xticks(range(len(data[container_col])))
    ax.set_xticklabels(data[container_col], rotation=45, ha='right', fontsize=9)
    
    # Ajout des valeurs sur les barres
    for i, bar in enumerate(bars):
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height + 1,
                f'{height:.1f}%', ha='center', va='bottom', fontsize=9, fontweight='bold')
    
    fig.tight_layout()
    return fig

def display_metrics(summary):
    """Affiche les métriques principales dans des cartes stylisées avec couleurs différentes"""
    col1, col2, col3, col4 = st.columns(4)
    
    # Style CSS personnalisé pour les cartes avec différentes couleurs
    st.markdown("""
        <style>
        .metric-card-1 {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border-radius: 10px;
            padding: 15px;
            text-align: center;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            color: white;
        }
        .metric-card-2 {
            background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
            border-radius: 10px;
            padding: 15px;
            text-align: center;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            color: white;
        }
        .metric-card-3 {
            background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
            border-radius: 10px;
            padding: 15px;
            text-align: center;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            color: white;
        }
        .metric-card-4 {
            background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%);
            border-radius: 10px;
            padding: 15px;
            text-align: center;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            color: white;
        }
        .metric-value {
            font-size: 28px;
            font-weight: bold;
            margin: 10px 0;
        }
        .metric-label {
            font-size: 14px;
            text-transform: uppercase;
            letter-spacing: 1px;
            opacity: 0.9;
        }
        </style>
    """, unsafe_allow_html=True)
    
    with col1:
        st.markdown(f"""
            <div class="metric-card-1">
                <div class="metric-label">📦 TOTAL CONTENEURS</div>
                <div class="metric-value">{len(summary)}</div>
            </div>
        """, unsafe_allow_html=True)
    
    with col2:
        avg_fill = summary["FILL_RATE_%"].mean()
        st.markdown(f"""
            <div class="metric-card-2">
                <div class="metric-label">📊 TAUX MOYEN</div>
                <div class="metric-value">{avg_fill:.1f}%</div>
            </div>
        """, unsafe_allow_html=True)
    
    with col3:
        compliant = len(summary[summary["FILL_RATE_%"] >= FILL_RATE_THRESHOLD])
        st.markdown(f"""
            <div class="metric-card-3">
                <div class="metric-label">✅ CONTENEURS CONFORMES</div>
                <div class="metric-value">{compliant}/{len(summary)}</div>
            </div>
        """, unsafe_allow_html=True)
    
    with col4:
        total_volume = summary["TOTAL_VOLUME"].sum()
        total_capacity = summary["CAPACITY"].sum()
        st.markdown(f"""
            <div class="metric-card-4">
                <div class="metric-label">📐 VOLUME TOTAL</div>
                <div class="metric-value">{total_volume:.1f} m³</div>
                <div class="metric-label">Capacité: {total_capacity:.0f} m³</div>
            </div>
        """, unsafe_allow_html=True)

def create_pdf(summary, full_title, chart_path, model, bl_no):
    """Génère le rapport PDF sur une seule page"""
    pdf = FPDF("P", "mm", "A4")
    pdf.add_page()
    
    # Entête avec logo (positionné en haut)
    logo_path = "entete.PNG"
    if os.path.exists(logo_path):
        pdf.image(logo_path, x=0, y=0, w=210, h=25)
        pdf.set_y(28)  # Position après le logo + un peu d'espace
    else:
        pdf.set_y(15)
    
    # Titre - avec un peu d'espace après le logo
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 8, full_title, ln=True, align="C")
    pdf.ln(5)
    
    # Métriques dans le PDF (sans couleurs - texte noir sur fond blanc)
    pdf.set_font("Arial", "B", 9)
    pdf.set_text_color(0, 0, 0)  # Noir
    pdf.set_fill_color(255, 255, 255)  # Blanc
    
    # Première ligne de métriques
    pdf.cell(95, 7, f"Total Conteneurs: {len(summary)}", border=1, fill=False, align="C")
    pdf.cell(95, 7, f"Taux Moyen: {summary['FILL_RATE_%'].mean():.1f}%", border=1, fill=False, align="C", ln=1)
    
    # Deuxième ligne de métriques
    compliant = len(summary[summary["FILL_RATE_%"] >= FILL_RATE_THRESHOLD])
    pdf.cell(95, 7, f"Conteneurs Conformes: {compliant}/{len(summary)}", border=1, fill=False, align="C")
    pdf.cell(95, 7, f"Volume Total: {summary['TOTAL_VOLUME'].sum():.1f} m³", border=1, fill=False, align="C", ln=1)
    
    pdf.ln(4)
    
    # Tableau compact avec colonne STATUS
    pdf.set_font("Arial", "B", 7)
    page_width = pdf.w - 20
    col_width = page_width / 6  # 6 colonnes maintenant (incluant STATUS)
    
    headers = ["CONTAINER NO", "SIZE", "TOTAL VOLUME", "CAPACITY", "FILL RATE", "STATUS"]
    
    # En-tête du tableau
    pdf.set_fill_color(200, 200, 200)
    for header in headers:
        pdf.cell(col_width, 6, header, border=1, align="C", fill=True)
    pdf.ln()
    
    # Corps du tableau
    pdf.set_font("Arial", "", 6.5)
    
    # Limiter la hauteur du tableau pour que tout tienne sur une page
    max_rows = min(len(summary), 12)  # Maximum 12 lignes pour rester sur une page
    
    for i in range(max_rows):
        row = summary.iloc[i]
        row_values = [
            str(row["CONTAINER NO"]),
            row["CTNER.SIZE"],
            f"{row['TOTAL_VOLUME']:.1f}",
            f"{row['CAPACITY']:.0f}",
            f"{row['FILL_RATE_%']:.1f}%",
            "OK" if "OK" in row["STATUS"] else "NON CONFORME"
        ]
        
        for j, value in enumerate(row_values):
            # Colorer la cellule STATUS
            if j == 5:  # Colonne STATUS
                if "OK" in value:
                    pdf.set_fill_color(144, 238, 144)  # Vert clair
                    pdf.set_text_color(0, 100, 0)
                else:
                    pdf.set_fill_color(255, 182, 193)  # Rose/rouge clair
                    pdf.set_text_color(200, 0, 0)
                pdf.cell(col_width, 5, value, border=1, align="C", fill=True)
            else:
                pdf.set_fill_color(255, 255, 255)
                pdf.set_text_color(0, 0, 0)
                pdf.cell(col_width, 5, value, border=1, align="C")
        pdf.ln()
    
    # Reset text color
    pdf.set_text_color(0, 0, 0)
    
    # Si plus de 12 conteneurs, ajouter un message
    if len(summary) > 12:
        pdf.set_font("Arial", "I", 7)
        pdf.cell(0, 5, f"... et {len(summary) - 12} autre(s) conteneur(s) non affiché(s)", ln=True, align="C")
    
    pdf.ln(3)
    
    # Graphique (redimensionné pour tenir sur la page)
    pdf.set_font("Arial", "B", 10)
    pdf.cell(0, 6, "Visualisation du taux de remplissage", ln=True, align="C")
    pdf.ln(2)
    
    # Calculer l'espace restant pour le graphique
    remaining_space = 297 - pdf.get_y() - 20  # Hauteur A4 moins marge
    chart_height = min(remaining_space, 80)  # Maximum 80mm pour le graphique
    
    pdf.image(chart_path, x=10, w=190, h=chart_height)
    
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
                
                # Métriques stylisées avec couleurs
                st.markdown("---")
                display_metrics(summary)
                
                # Affichage du tableau des résultats
                st.markdown("---")
                st.subheader("📊 Résultats par conteneur")
                
                # Affichage du tableau complet
                display_df = summary[["CONTAINER NO", "CTNER.SIZE", "TOTAL_VOLUME", "CAPACITY", "FILL_RATE_%", "STATUS"]].copy()
                st.dataframe(display_df, use_container_width=True)
                
                # Graphique avec labels diagonaux
                st.subheader("📈 Taux de remplissage")
                fig = create_chart(summary, "CONTAINER NO", "FILL_RATE_%")
                st.pyplot(fig)
                plt.close(fig)
                
                # Génération du PDF
                st.markdown("---")
                st.subheader("📄 Export du rapport")
                
                # Sauvegarde temporaire du graphique pour le PDF
                with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp_img:
                    # Créer un graphique plus petit pour le PDF
                    fig_pdf, ax_pdf = plt.subplots(figsize=(10, 4))
                    bars = ax_pdf.bar(range(len(summary["CONTAINER NO"])), summary["FILL_RATE_%"], 
                                      color=['#2ecc71' if x >= FILL_RATE_THRESHOLD else '#e74c3c' 
                                             for x in summary["FILL_RATE_%"]], 
                                      alpha=0.8, edgecolor='black', linewidth=1)
                    ax_pdf.axhline(y=FILL_RATE_THRESHOLD, color='red', linestyle='--', linewidth=2)
                    ax_pdf.set_ylim(0, 100)
                    ax_pdf.set_ylabel("Taux de remplissage (%)")
                    ax_pdf.set_xlabel("Numéro du conteneur")
                    ax_pdf.set_title("Taux de Remplissage par Conteneur")
                    ax_pdf.set_xticks(range(len(summary["CONTAINER NO"])))
                    ax_pdf.set_xticklabels(summary["CONTAINER NO"], rotation=45, ha='right', fontsize=8)
                    ax_pdf.grid(True, alpha=0.3, axis='y')
                    fig_pdf.tight_layout()
                    fig_pdf.savefig(tmp_img.name, dpi=200, bbox_inches="tight")
                    plt.close(fig_pdf)
                    
                    # Création du PDF
                    pdf_bytes = create_pdf(summary, full_title, tmp_img.name, model, bl_no)
                    
                    # Nettoyage
                    os.unlink(tmp_img.name)
                
                # Bouton de téléchargement
                col1, col2, col3 = st.columns([1, 2, 1])
                with col2:
                    st.download_button(
                        label="📥 Télécharger le rapport PDF",
                        data=pdf_bytes,
                        file_name=f"{model}_{bl_no}_dashboard.pdf",
                        mime="application/pdf",
                        use_container_width=True,
                        type="primary"
                    )
                
                # Message d'information sur le PDF
                if len(summary) > 12:
                    st.info(f"💡 Note: Le PDF affiche les {min(12, len(summary))} premiers conteneurs sur {len(summary)} pour rester sur une seule page. Les métriques globales restent complètes.")
                
            else:
                st.error("❌ Colonne 'CBM' introuvable. Vérifiez que votre fichier contient une colonne avec 'CBM' dans son nom.")
        
        except Exception as e:
            st.error(f"❌ Erreur lors du traitement du fichier : {str(e)}")
            st.info("Vérifiez le format de votre fichier Excel (colonnes requises : CONTAINER NO, CTNER.SIZE, [CBM])")

if __name__ == "__main__":
    main()
