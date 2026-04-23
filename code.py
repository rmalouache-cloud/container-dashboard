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
# DICTIONNAIRES DE TRADUCTION
# =========================
def get_text(lang):
    """Retourne les textes selon la langue choisie"""
    texts = {
        'fr': {
            'title': "📦 Tableau de Bord Industriel - Remplissage Conteneur",
            'subtitle': "Analyse Supply Chain - Contrôle BOM & Emballage",
            'user_guide': "📘 Manuel d'utilisation",
            'guide_content': """
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
            """,
            'study_info': "📦 Informations d'étude",
            'packing_type': "Type de liste de colisage",
            'model': "Modèle",
            'bl_no': "N° BL",
            'raw_data': "🔍 Aperçu des données brutes",
            'results': "📊 Résultats par conteneur",
            'fill_rate': "📈 Taux de remplissage",
            'export': "📄 Export du rapport",
            'download': "📥 Télécharger le rapport PDF",
            'total_containers': "📦 TOTAL CONTENEURS",
            'avg_rate': "📊 TAUX MOYEN",
            'compliant': "✅ CONTENEURS CONFORMES",
            'total_volume': "📐 VOLUME TOTAL",
            'capacity': "Capacité",
            'status_ok': "OK",
            'status_nok': "NON CONFORME",
            'threshold': "Seuil",
            'fill_rate_chart': "Taux de Remplissage par Conteneur",
            'fill_rate_percent': "Taux de remplissage (%)",
            'container_no': "Numéro du conteneur",
            'note': "💡 Note: Le PDF affiche les",
            'first_containers': "premiers conteneurs sur",
            'to_fit': "pour rester sur une seule page. Les métriques globales restent complètes.",
            'error_cbm': "❌ Colonne 'CBM' introuvable. Vérifiez que votre fichier contient une colonne avec 'CBM' dans son nom.",
            'error_file': "❌ Erreur lors du traitement du fichier",
            'error_format': "Vérifiez le format de votre fichier Excel (colonnes requises : CONTAINER NO, CTNER.SIZE, [CBM])",
            'loading': "Chargement et analyse des données...",
            'upload': "📂 Télécharger fichier Excel",
            'upload_help': "Format attendu : Excel avec colonnes CONTAINER NO, CTNER.SIZE, et une colonne contenant 'CBM'",
            'language': "🌐 Langue / Language",
            'visualization': "Visualisation du taux de remplissage",
            'size': "Taille",
            'total_vol': "Volume total",
            'fill_rate_pdf': "Taux de remplissage",
            'status': "Statut",
            'and': "et",
            'other_containers': "autre(s) conteneur(s) non affiché(s)"
        },
        'en': {
            'title': "📦 Container Filling Industrial Dashboard",
            'subtitle': "Supply Chain Analysis - BOM & Packing Control",
            'user_guide': "📘 User Guide",
            'guide_content': """
            ### 📋 Instructions
            
            1. **Study Information** : Fill in the basic information
            2. **File Import** : Upload your Excel file with container data
            3. **Automatic Analysis** : The dashboard automatically calculates:
               - Total volume per container
               - Fill rate
               - Compliance (OK if ≥70%)
            
            ### 📊 Expected Excel File Format
            - Required columns: `CONTAINER NO`, `CTNER.SIZE`, `[CBM]`
            - File must contain a column with "CBM" in its name
            - Supported container sizes: 20GP, 40GP, 40HQ
            """,
            'study_info': "📦 Study Information",
            'packing_type': "Type of Packing List",
            'model': "Model",
            'bl_no': "BL No",
            'raw_data': "🔍 Raw Data Preview",
            'results': "📊 Container Results",
            'fill_rate': "📈 Fill Rate",
            'export': "📄 Export Report",
            'download': "📥 Download PDF Report",
            'total_containers': "📦 TOTAL CONTAINERS",
            'avg_rate': "📊 AVERAGE RATE",
            'compliant': "✅ COMPLIANT CONTAINERS",
            'total_volume': "📐 TOTAL VOLUME",
            'capacity': "Capacity",
            'status_ok': "OK",
            'status_nok': "NON COMPLIANT",
            'threshold': "Threshold",
            'fill_rate_chart': "Container Fill Rate",
            'fill_rate_percent': "Fill Rate (%)",
            'container_no': "Container Number",
            'note': "💡 Note: PDF shows first",
            'first_containers': "containers out of",
            'to_fit': "to fit on one page. Global metrics remain complete.",
            'error_cbm': "❌ 'CBM' column not found. Make sure your file contains a column with 'CBM' in its name.",
            'error_file': "❌ Error processing file",
            'error_format': "Check your Excel file format (required columns: CONTAINER NO, CTNER.SIZE, [CBM])",
            'loading': "Loading and analyzing data...",
            'upload': "📂 Upload Excel File",
            'upload_help': "Expected format: Excel with columns CONTAINER NO, CTNER.SIZE, and a column containing 'CBM'",
            'language': "🌐 Language",
            'visualization': "Fill Rate Visualization",
            'size': "Size",
            'total_vol': "Total Volume",
            'fill_rate_pdf': "Fill Rate",
            'status': "Status",
            'and': "and",
            'other_containers': "other container(s) not shown"
        }
    }
    return texts[lang]

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

def create_chart(data, container_col, fill_rate_col, threshold=FILL_RATE_THRESHOLD, lang='en'):
    """Crée le graphique du taux de remplissage avec texte diagonal pour les labels"""
    texts = get_text(lang)
    fig, ax = plt.subplots(figsize=(12, 6))
    
    # Création des barres
    bars = ax.bar(range(len(data[container_col])), data[fill_rate_col], 
                  color=['#2ecc71' if x >= threshold else '#e74c3c' 
                         for x in data[fill_rate_col]], 
                  alpha=0.8, edgecolor='black', linewidth=1)
    
    # Ligne de seuil
    ax.axhline(y=threshold, color='red', linestyle='--', 
               linewidth=2, label=f'{texts["threshold"]} ({threshold}%)', zorder=5)
    
    # Configuration des axes
    ax.set_ylim(0, 100)
    ax.set_ylabel(texts["fill_rate_percent"], fontsize=12, fontweight='bold')
    ax.set_xlabel(texts["container_no"], fontsize=12, fontweight='bold')
    ax.set_title(texts["fill_rate_chart"], fontsize=14, fontweight='bold')
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

def display_metrics(summary, lang='en'):
    """Affiche les métriques principales dans des cartes stylisées avec couleurs différentes"""
    texts = get_text(lang)
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
                <div class="metric-label">{texts['total_containers']}</div>
                <div class="metric-value">{len(summary)}</div>
            </div>
        """, unsafe_allow_html=True)
    
    with col2:
        avg_fill = summary["FILL_RATE_%"].mean()
        st.markdown(f"""
            <div class="metric-card-2">
                <div class="metric-label">{texts['avg_rate']}</div>
                <div class="metric-value">{avg_fill:.1f}%</div>
            </div>
        """, unsafe_allow_html=True)
    
    with col3:
        compliant = len(summary[summary["FILL_RATE_%"] >= FILL_RATE_THRESHOLD])
        st.markdown(f"""
            <div class="metric-card-3">
                <div class="metric-label">{texts['compliant']}</div>
                <div class="metric-value">{compliant}/{len(summary)}</div>
            </div>
        """, unsafe_allow_html=True)
    
    with col4:
        total_volume = summary["TOTAL_VOLUME"].sum()
        total_capacity = summary["CAPACITY"].sum()
        st.markdown(f"""
            <div class="metric-card-4">
                <div class="metric-label">{texts['total_volume']}</div>
                <div class="metric-value">{total_volume:.1f} m³</div>
                <div class="metric-label">{texts['capacity']}: {total_capacity:.0f} m³</div>
            </div>
        """, unsafe_allow_html=True)

def create_pdf(summary, full_title, chart_path, model, bl_no, lang='en'):
    """Génère le rapport PDF sur une seule page"""
    texts = get_text(lang)
    pdf = FPDF("P", "mm", "A4")
    pdf.add_page()
    
    # Entête avec logo (positionné en haut)
    logo_path = "entete.PNG"
    if os.path.exists(logo_path):
        pdf.image(logo_path, x=0, y=0, w=210, h=25)
        pdf.set_y(28)
    else:
        pdf.set_y(15)
    
    # Titre
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 8, full_title, ln=True, align="C")
    pdf.ln(5)
    
    # Métriques dans le PDF (sans couleurs)
    pdf.set_font("Arial", "B", 9)
    pdf.set_text_color(0, 0, 0)
    pdf.set_fill_color(255, 255, 255)
    
    # Première ligne de métriques
    pdf.cell(95, 7, f"{texts['total_containers'].replace('📦', '').strip()}: {len(summary)}", border=1, fill=False, align="C")
    pdf.cell(95, 7, f"{texts['avg_rate'].replace('📊', '').strip()}: {summary['FILL_RATE_%'].mean():.1f}%", border=1, fill=False, align="C", ln=1)
    
    # Deuxième ligne de métriques
    compliant = len(summary[summary["FILL_RATE_%"] >= FILL_RATE_THRESHOLD])
    pdf.cell(95, 7, f"{texts['compliant'].replace('✅', '').strip()}: {compliant}/{len(summary)}", border=1, fill=False, align="C")
    pdf.cell(95, 7, f"{texts['total_volume'].replace('📐', '').strip()}: {summary['TOTAL_VOLUME'].sum():.1f} m³", border=1, fill=False, align="C", ln=1)
    
    pdf.ln(4)
    
    # Tableau compact avec colonne STATUS
    pdf.set_font("Arial", "B", 7)
    page_width = pdf.w - 20
    col_width = page_width / 6
    
    headers = [texts['container_no'].replace('Numéro du conteneur', 'CONTAINER NO').replace('Container Number', 'CONTAINER NO'),
               texts['size'].upper() if lang == 'fr' else "SIZE",
               texts['total_vol'].upper() if lang == 'fr' else "TOTAL VOLUME",
               texts['capacity'].upper(),
               texts['fill_rate_pdf'].upper(),
               texts['status'].upper()]
    
    # En-tête du tableau
    pdf.set_fill_color(200, 200, 200)
    for header in headers:
        pdf.cell(col_width, 6, header, border=1, align="C", fill=True)
    pdf.ln()
    
    # Corps du tableau
    pdf.set_font("Arial", "", 6.5)
    max_rows = min(len(summary), 12)
    
    for i in range(max_rows):
        row = summary.iloc[i]
        row_values = [
            str(row["CONTAINER NO"]),
            row["CTNER.SIZE"],
            f"{row['TOTAL_VOLUME']:.1f}",
            f"{row['CAPACITY']:.0f}",
            f"{row['FILL_RATE_%']:.1f}%",
            texts['status_ok'] if "OK" in row["STATUS"] else texts['status_nok']
        ]
        
        for j, value in enumerate(row_values):
            if j == 5:
                if "OK" in row["STATUS"]:
                    pdf.set_fill_color(144, 238, 144)
                    pdf.set_text_color(0, 100, 0)
                else:
                    pdf.set_fill_color(255, 182, 193)
                    pdf.set_text_color(200, 0, 0)
                pdf.cell(col_width, 5, value, border=1, align="C", fill=True)
            else:
                pdf.set_fill_color(255, 255, 255)
                pdf.set_text_color(0, 0, 0)
                pdf.cell(col_width, 5, value, border=1, align="C")
        pdf.ln()
    
    pdf.set_text_color(0, 0, 0)
    
    if len(summary) > 12:
        pdf.set_font("Arial", "I", 7)
        pdf.cell(0, 5, f"... {texts['and']} {len(summary) - 12} {texts['other_containers']}", ln=True, align="C")
    
    pdf.ln(3)
    
    # Graphique
    pdf.set_font("Arial", "B", 10)
    pdf.cell(0, 6, texts['visualization'], ln=True, align="C")
    pdf.ln(2)
    
    remaining_space = 297 - pdf.get_y() - 20
    chart_height = min(remaining_space, 80)
    pdf.image(chart_path, x=10, w=190, h=chart_height)
    
    return pdf.output(dest="S").encode("latin1")

# =========================
# AFFICHAGE DES LOGOS
# =========================
def display_header(lang='en'):
    """Affiche l'en-tête avec les logos"""
    texts = get_text(lang)
    try:
        container_logo = Image.open("conteneur_logo.png")
        stream_logo = Image.open("stream_logo.png")
        
        col1, col2, col3 = st.columns([1, 5, 1])
        
        with col1:
            st.image(container_logo, width=150)
        with col2:
            st.title(texts['title'])
            st.caption(texts['subtitle'])
        with col3:
            st.image(stream_logo, width=150)
    except FileNotFoundError:
        st.title(texts['title'])
        st.caption(texts['subtitle'])

# =========================
# GUIDE UTILISATEUR
# =========================
def display_user_guide(lang='en'):
    """Affiche le guide utilisateur"""
    texts = get_text(lang)
    with st.expander(texts['user_guide']):
        st.markdown(texts['guide_content'])

# =========================
# APPLICATION PRINCIPALE
# =========================
def main():
    """Fonction principale de l'application"""
    
    # Sélecteur de langue dans la barre latérale
    with st.sidebar:
        st.markdown("### 🌐 Language / Langue")
        language = st.radio(
            "",
            options=['🇫🇷 Français', '🇬🇧 English'],
            index=1
        )
        lang = 'fr' if 'Français' in language else 'en'
        st.markdown("---")
    
    texts = get_text(lang)
    
    # En-tête
    display_header(lang)
    
    # Guide utilisateur
    display_user_guide(lang)
    
    # Formulaire d'informations
    with st.container():
        st.markdown(f"### {texts['study_info']}")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            packing_type = st.selectbox(
                texts['packing_type'],
                ["Panel", "SP", "SP/MainBoard", "OC"],
                help=texts['packing_type']
            )
        
        with col2:
            model = st.text_input(texts['model'], placeholder=texts['model'])
        
        with col3:
            bl_no = st.text_input(texts['bl_no'], placeholder=texts['bl_no'])
    
    st.markdown("---")
    
    # Titre dynamique
    if model and bl_no:
        if lang == 'fr':
            full_title = f"Tableau de Bord - Remplissage Conteneur {packing_type} de {model}__{bl_no}"
        else:
            full_title = f"Container Filling Dashboard of {packing_type} of {model}__{bl_no}"
    else:
        full_title = texts['title'] if lang == 'en' else "Tableau de Bord - Remplissage Conteneur"
    
    st.subheader(full_title)
    
    # Upload du fichier
    file = st.file_uploader(
        texts['upload'], 
        type=["xlsx"],
        help=texts['upload_help']
    )
    
    if file is not None:
        try:
            # Chargement des données
            with st.spinner(texts['loading']):
                df = load_excel(file)
            
            # Aperçu des données
            with st.expander(texts['raw_data']):
                st.dataframe(df, use_container_width=True)
            
            # Recherche de la colonne CBM
            cbm_col = next((col for col in df.columns if "CBM" in col.upper()), None)
            
            if cbm_col:
                # Calcul du résumé
                summary = calculate_summary(df, cbm_col)
                
                # Métriques stylisées
                st.markdown("---")
                display_metrics(summary, lang)
                
                # Affichage du tableau des résultats
                st.markdown("---")
                st.subheader(texts['results'])
                
                # Affichage du tableau complet
                display_df = summary[["CONTAINER NO", "CTNER.SIZE", "TOTAL_VOLUME", "CAPACITY", "FILL_RATE_%", "STATUS"]].copy()
                st.dataframe(display_df, use_container_width=True)
                
                # Graphique
                st.subheader(texts['fill_rate'])
                fig = create_chart(summary, "CONTAINER NO", "FILL_RATE_%", lang=lang)
                st.pyplot(fig)
                plt.close(fig)
                
                # Génération du PDF
                st.markdown("---")
                st.subheader(texts['export'])
                
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
                    ax_pdf.set_ylabel(texts['fill_rate_percent'])
                    ax_pdf.set_xlabel(texts['container_no'])
                    ax_pdf.set_title(texts['fill_rate_chart'])
                    ax_pdf.set_xticks(range(len(summary["CONTAINER NO"])))
                    ax_pdf.set_xticklabels(summary["CONTAINER NO"], rotation=45, ha='right', fontsize=8)
                    ax_pdf.grid(True, alpha=0.3, axis='y')
                    fig_pdf.tight_layout()
                    fig_pdf.savefig(tmp_img.name, dpi=200, bbox_inches="tight")
                    plt.close(fig_pdf)
                    
                    # Création du PDF
                    pdf_bytes = create_pdf(summary, full_title, tmp_img.name, model, bl_no, lang)
                    
                    # Nettoyage
                    os.unlink(tmp_img.name)
                
                # Bouton de téléchargement
                col1, col2, col3 = st.columns([1, 2, 1])
                with col2:
                    st.download_button(
                        label=texts['download'],
                        data=pdf_bytes,
                        file_name=f"{model}_{bl_no}_dashboard.pdf",
                        mime="application/pdf",
                        use_container_width=True,
                        type="primary"
                    )
                
                # Message d'information sur le PDF
                if len(summary) > 12:
                    st.info(f"{texts['note']} {min(12, len(summary))} {texts['first_containers']} {len(summary)} {texts['to_fit']}")
                
            else:
                st.error(texts['error_cbm'])
        
        except Exception as e:
            st.error(f"{texts['error_file']} : {str(e)}")
            st.info(texts['error_format'])

if __name__ == "__main__":
    main()
