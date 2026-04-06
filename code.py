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
    st.markdown("Guide utilisateur ici...")

# =========================
# INPUTS
# =========================
st.markdown("### 📦 Study Information")

packing_type = st.selectbox(
    "Type of Packing List",
    ["Panel", "SP", "SP/MainBoard", "OC"]
)

model = st.text_input("Model")
BL No = st.text_input("BL No")

st.markdown("---")

# =========================
# TITLE
# =========================
if model and BL No:
    full_title = f"Container Filling Industrial Dashboard of {packing_type} of {model}__{BL No}"
else:
    full_title = "Container Filling Industrial Dashboard"

st.subheader(full_title)

# =========================
# UPLOAD
# =========================
file = st.file_uploader("Upload Excel", type=["xlsx"])

summary = None

if file is not None:

    df = pd.read_excel(file)
    df.columns = df.columns.str.strip()

    st.dataframe(df)

    cbm_col = next((col for col in df.columns if "CBM" in col.upper()), None)

    if cbm_col:

        summary = df.groupby(
            ["CONTAINER NO", "CTNER.SIZE"], as_index=False
        ).agg({cbm_col: "sum"})

        summary.rename(columns={cbm_col: "TOTAL_VOLUME"}, inplace=True)

        capacity_map = {"20GP": 33, "40GP": 67, "40HQ": 76}
        summary["CAPACITY"] = summary["CTNER.SIZE"].map(capacity_map)

        summary["FILL_RATE_%"] = summary["TOTAL_VOLUME"] * 100 / summary["CAPACITY"]

        summary["STATUS"] = summary["FILL_RATE_%"].apply(
            lambda x: "OK" if x >= 70 else "NON CONFORME"
        )

        st.subheader("📊 Result Table")
        st.dataframe(summary)

        # =========================
        # DIAGRAMME
        # =========================
        st.subheader("📈 Filling Rate Chart")

        plt.close('all')

        fig, ax = plt.subplots(figsize=(8, 4))

        ax.bar(summary["CONTAINER NO"], summary["FILL_RATE_%"])
        ax.axhline(y=70, color='red', linestyle='--', linewidth=3, zorder=5)

        ax.set_ylim(0, 100)
        ax.set_title("Filling Rate (%)")
        ax.set_ylabel("%")
        ax.set_xlabel("Container")

        fig.tight_layout()
        st.pyplot(fig)

# =========================
# PDF
# =========================
if summary is not None:

    pdf = FPDF("P", "mm", "A4")
    pdf.add_page()

    logo_path = "entete.PNG"

    if os.path.exists(logo_path):
        pdf.image(logo_path, x=0, y=0, w=210, h=25)

    pdf.ln(55)

    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 10, full_title, ln=True, align="C")

    pdf.ln(5)

    pdf.set_font("Arial", "B", 7)

    page_width = pdf.w - 20
    col_width = page_width / len(summary.columns)

    headers = ["CONTAINER NO", "SIZE", "TOTAL_VOL", "CAPACITY", "FILL_RATE %", "STATUS"]

    for col in headers:
        pdf.cell(col_width, 6, col, border=1, align="C")

    pdf.ln()

    pdf.set_font("Arial", "", 7)

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
                pdf.set_text_color(0, 150, 0) if val == "OK" else pdf.set_text_color(255, 0, 0)
            else:
                pdf.set_text_color(0, 0, 0)

            pdf.cell(col_width, 6, str(val), border=1, align="C")

        pdf.ln()

    tmp_img = tempfile.NamedTemporaryFile(delete=False, suffix=".png")

    fig, ax = plt.subplots(figsize=(6, 3))
    ax.bar(summary["CONTAINER NO"], summary["FILL_RATE_%"])
    ax.axhline(y=70, color='red', linestyle='--', linewidth=3)

    fig.tight_layout()
    fig.savefig(tmp_img.name, dpi=300, bbox_inches="tight")
    plt.close(fig)

    pdf.ln(3)
    pdf.image(tmp_img.name, x=10, w=180)

    # ✅ CORRECTION ICI (anti None)
    pdf_bytes = pdf.output(dest="S").encode("latin1")

    st.download_button(
        label="📄 Download PDF",
        data=pdf_bytes,
        file_name=f"{model}_{BL No}_dashboard.pdf",
        mime="application/pdf"
    )
