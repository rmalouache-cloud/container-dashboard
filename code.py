import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from fpdf import FPDF
import tempfile
import os

# =========================
# CONFIG
# =========================
st.set_page_config(page_title="Container Dashboard", layout="wide")

# =========================
# HEADER
# =========================
col1, col2, col3 = st.columns([1, 5, 1])

with col1:
    st.write("📦")

with col2:
    st.title("Container Filling Industrial Dashboard")

with col3:
    st.write("📊")

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

    # =========================
    # CBM COLUMN
    # =========================
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
# PDF
# =========================
if summary is not None:

    pdf = FPDF(orientation="L", unit="mm", format="A4")  # ✅ LANDSCAPE
    pdf.add_page()

    # =========================
    # HEADER IMAGE (ENTETE)
    # =========================
    entete_path = "entete/entete.png"  # chemin GitHub

    if os.path.exists(entete_path):
        pdf.image(entete_path, x=10, y=8, w=60)

    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, full_title, ln=True, align="C")
    pdf.ln(10)

    # =========================
    # TABLE (AUTO WIDTH FIX)
    # =========================
    pdf.set_font("Arial", "B", 8)

    table_width = 270
    col_width = table_width / len(summary.columns)

    headers = ["CONTAINER NO", "SIZE", "TOTAL_VOL", "CAPACITY", "FILL_RATE %", "STATUS"]

    for col in headers:
        pdf.cell(col_width, 8, col, border=1, align="C")
    pdf.ln()

    pdf.set_font("Arial", "", 8)

    for _, row in summary.iterrows():

        row_values = [
            row["CONTAINER NO"],
            row["CTNER.SIZE"],
            f"{row['TOTAL_VOLUME']:.2f}",
            f"{row['CAPACITY']:.0f}",
            f"{row['FILL_RATE_%']:.2f}%",
            row["STATUS"]
        ]

        for i, val in enumerate(row_values):

            if headers[i] == "STATUS":
                if val == "OK":
                    pdf.set_text_color(0, 150, 0)
                else:
                    pdf.set_text_color(255, 0, 0)
            else:
                pdf.set_text_color(0, 0, 0)

            pdf.cell(col_width, 8, str(val), border=1, align="C")

        pdf.ln()

    # =========================
    # CHART
    # =========================
    pdf.ln(10)
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 10, "Filling Rate Chart", ln=True)

    tmp_img = tempfile.NamedTemporaryFile(delete=False, suffix=".png")

    fig, ax = plt.subplots(figsize=(8, 4))
    ax.bar(summary["CONTAINER NO"], summary["FILL_RATE_%"])
    ax.axhline(70, linestyle="--")
    ax.set_title("Container Filling Rate")
    ax.set_ylabel("%")

    fig.tight_layout()
    fig.savefig(tmp_img.name, dpi=300, bbox_inches="tight")
    plt.close(fig)

    pdf.image(tmp_img.name, x=10, w=250)

    # =========================
    # SAVE PDF
    # =========================
    tmp_pdf = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    pdf.output(tmp_pdf.name)

    with open(tmp_pdf.name, "rb") as f:
        st.download_button(
            label="📄 Download PDF",
            data=f,
            file_name=f"{model}_{odf}_dashboard.pdf"
        )
