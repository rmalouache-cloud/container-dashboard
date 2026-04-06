import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from PIL import Image
from fpdf import FPDF
import tempfile
import os

# =========================
# CONFIG
# =========================
st.set_page_config(page_title="Container Dashboard", layout="wide")

# =========================
# LOGOS + HEADER
# =========================
container_logo = Image.open("conteneur_logo.png")
stream_logo = Image.open("stream_logo.png")

col1, col2, col3 = st.columns([1, 5, 1])

with col1:
    st.image(container_logo, width=200)

with col2:
    st.title(" Container Filling Industrial Dashboard")
    st.caption("Supply Chain Analysis - BOM & Packing Control")

with col3:
    st.image(stream_logo, width=200)

# =========================
# USER GUIDE
# =========================
with st.expander("📘 Manuel d'utilisation / User Guide"):
    st.markdown("""
# 🇫🇷 Manuel d'utilisation

### 🎯 Objectif
Analyser le taux de remplissage des conteneurs à partir d’un fichier Excel.

### 📂 Format requis
- CONTAINER NO  
- CTNER.SIZE (20GP, 40GP, 40HQ)  
- CBM  

### 🚀 Étapes
1. Upload fichier Excel  
2. Vérifier les données  
3. Lire les résultats  
4. Visualiser graphique  
5. Télécharger Excel ou PDF  

### 📏 Règles
- 20GP → 33  
- 40GP → 67  
- 40HQ → 76  

👉 OK ≥ 70%  
👉 NON CONFORME < 70%  

---

# 🇬🇧 User Guide

### 🎯 Purpose
Analyze container filling rate from an Excel file.

### 📂 Required columns
- CONTAINER NO  
- CTNER.SIZE  
- CBM  

### 🚀 Steps
1. Upload Excel file  
2. Check preview  
3. Analyze results  
4. View chart  
5. Download Excel/PDF  
""")

# =========================
# INPUTS
# =========================
st.markdown("### 📦 Study Information")

packing_type = st.selectbox(
    "Type of Packing List",
    ["Panel", "SP", "SP/MainBoard", "OC"]
)

model = st.text_input("Model (ex: Mini LED)")
odf = st.text_input("ODF (ex: IDL2500)")

st.markdown("---")

# =========================
# TITLE
# =========================
if model and odf:
    full_title = f"Container Filling Industrial Dashboard of {packing_type} of {model}__{odf}"
else:
    full_title = "Container Filling Industrial Dashboard"

st.subheader(full_title)

# =========================
# UPLOAD
# =========================
file = st.file_uploader("Upload Packing Excel file", type=["xlsx"])

summary = None

if file is not None:

    df = pd.read_excel(file)
    df.columns = df.columns.str.strip()

    st.write("📄 Data Preview")
    st.dataframe(df)

    cbm_col = next((col for col in df.columns if "CBM" in col.upper()), None)

    if cbm_col is None:
        st.error("❌ CBM column not found")
    else:

        summary = df.groupby(
            ["CONTAINER NO", "CTNER.SIZE"], as_index=False
        ).agg({cbm_col: "sum"})

        summary.rename(columns={cbm_col: "TOTAL_VOLUME"}, inplace=True)

        capacity_map = {"20GP": 33, "40GP": 67, "40HQ": 76}

        summary["CAPACITY"] = summary["CTNER.SIZE"].map(capacity_map)

        summary["FILL_RATE_%"] = (
            summary["TOTAL_VOLUME"] * 100 / summary["CAPACITY"]
        )

        summary["STATUS"] = summary["FILL_RATE_%"].apply(
            lambda x: "OK" if x >= 70 else "NON CONFORME"
        )

        st.subheader("📊 Result Table")
        st.dataframe(summary)

        # =========================
        # 📈 DIAGRAMME (FIXED)
        # =========================
        st.subheader("📈 Filling Rate Chart")

        fig, ax = plt.subplots(figsize=(8, 4))

        ax.bar(summary["CONTAINER NO"], summary["FILL_RATE_%"])
        ax.axhline(70, linestyle="--")
        ax.set_title("Filling Rate (%)")
        ax.set_ylabel("%")
        ax.set_xlabel("Container")

        fig.tight_layout()

        st.pyplot(fig)  # ✅ IMPORTANT

# =========================
# PDF GENERATION (CORRIGÉ)
# =========================
if summary is not None:

    pdf = FPDF(orientation="P", unit="mm", format="A4")  # ✅ NORMAL (portrait)
    pdf.add_page()

    # =========================
    # ENTETE (IMAGE)
    # =========================
    logo_path = "entete.PNG"

    if os.path.exists(logo_path):
        pdf.image(logo_path, x=50, y=50, w=60)  # taille + position

    # =========================
    # TITLE
    # =========================
    pdf.set_font("Arial", "B", 12)
    pdf.ln(25)  # espace après entete
    pdf.cell(0, 10, full_title, ln=True, align="C")

    pdf.ln(5)

    # =========================
    # TABLEAU (AJUSTÉ POUR PAGE)
    # =========================
    pdf.set_font("Arial", "B", 7)

    page_width = pdf.w - 20
    col_width = page_width / len(summary.columns)

    headers = ["CONTAINER NO", "SIZE", "TOTAL_VOL", "CAPACITY", "FILL_RATE %", "STATUS"]

    for col in headers:
        pdf.cell(col_width, 6, col, border=1, align="C")

    pdf.ln()

    pdf.set_font("Arial", "", 7)

    # limiter nombre de lignes pour rester sur 1 page
    max_rows = 8

    for i, (_, row) in enumerate(summary.iterrows()):
        if i >= max_rows:
            break

        row_values = [
            row["CONTAINER NO"],
            row["CTNER.SIZE"],
            f"{row['TOTAL_VOLUME']:.2f}",
            f"{row['CAPACITY']:.0f}",
            f"{row['FILL_RATE_%']:.2f}%",
            row["STATUS"]
        ]

        for j, val in enumerate(row_values):

            if headers[j] == "STATUS":
                if val == "OK":
                    pdf.set_text_color(0, 150, 0)
                else:
                    pdf.set_text_color(255, 0, 0)
            else:
                pdf.set_text_color(0, 0, 0)

            pdf.cell(col_width, 6, str(val), border=1, align="C")

        pdf.ln()

    # =========================
    # GRAPH (SUR MÊME PAGE)
    # =========================
    tmp_img = tempfile.NamedTemporaryFile(delete=False, suffix=".png")

    fig, ax = plt.subplots(figsize=(6, 3))

    ax.bar(summary["CONTAINER NO"], summary["FILL_RATE_%"])
    ax.axhline(70, linestyle="--")
    ax.set_title("Filling Rate (%)")
    ax.set_ylabel("%")

    fig.tight_layout()
    fig.savefig(tmp_img.name, dpi=300, bbox_inches="tight")
    plt.close(fig)

    # placement du graphique sous le tableau
    pdf.ln(3)
    pdf.image(tmp_img.name, x=10, w=180)

    # =========================
    # DOWNLOAD
    # =========================
    tmp_pdf = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    pdf.output(tmp_pdf.name)

    with open(tmp_pdf.name, "rb") as f:
        st.download_button(
            label="📄 Download PDF",
            data=f,
            file_name=f"{model}_{odf}_dashboard.pdf"
        )
