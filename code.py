import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from PIL import Image
from fpdf import FPDF
import tempfile

# =========================
# CONFIG
# =========================
st.set_page_config(page_title="Container Dashboard", layout="wide")

# =========================
# SESSION STATE
# =========================
if "packing_type" not in st.session_state:
    st.session_state.packing_type = "Panel"

if "model" not in st.session_state:
    st.session_state.model = ""

if "odf" not in st.session_state:
    st.session_state.odf = ""

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
# INPUT FIELDS
# =========================
st.markdown("### 📦 Study Information")

packing_type = st.selectbox(
    "Type of Packing List",
    ["Panel", "SP", "SP/MainBoard", "OC"],
    key="packing_type"
)

model = st.text_input("Model (ex: Mini LED)", key="model")
odf = st.text_input("ODF (ex: IDL2500)", key="odf")

st.markdown("---")

# =========================
# DYNAMIC TITLE
# =========================
if st.session_state.model and st.session_state.odf:
    full_title = f"Container Filling Industrial Dashboard of {st.session_state.packing_type} of {st.session_state.model}__{st.session_state.odf}"
else:
    full_title = "Container Filling Industrial Dashboard"

st.subheader(full_title)

# =========================
# UPLOAD FILE
# =========================
file = st.file_uploader("Upload Packing Excel file", type=["xlsx"])

summary = None

if file is not None:

    df = pd.read_excel(file)
    df.columns = df.columns.str.strip()

    st.write("📄 Data Preview")
    st.dataframe(df)

    # =========================
    # DETECT CBM COLUMN
    # =========================
    cbm_col = None
    for col in df.columns:
        if "CBM" in col.upper():
            cbm_col = col
            break

    if cbm_col is None:
        st.error("❌ CBM column not found")
    else:

        # =========================
        # GROUP DATA
        # =========================
        summary = df.groupby(
            ["CONTAINER NO", "CTNER.SIZE"], as_index=False
        ).agg({cbm_col: "sum"})

        summary.rename(columns={cbm_col: "TOTAL_VOLUME"}, inplace=True)

        # =========================
        # CAPACITY
        # =========================
        capacity_map = {
            "20GP": 33,
            "40GP": 67,
            "40HQ": 76
        }

        summary["CAPACITY"] = summary["CTNER.SIZE"].map(capacity_map)

        # =========================
        # FILL RATE
        # =========================
        summary["FILL_RATE_%"] = summary["TOTAL_VOLUME"] * 100 / summary["CAPACITY"]

        # =========================
        # STATUS
        # =========================
        summary["STATUS"] = summary["FILL_RATE_%"].apply(
            lambda x: "OK" if x >= 70 else "NON CONFORME"
        )

        st.subheader("📊 Result Table")
        st.dataframe(summary)

        # =========================
        # CHART
        # =========================
        st.subheader("📈 Filling Rate Chart")

        fig, ax = plt.subplots()
        ax.bar(summary["CONTAINER NO"], summary["FILL_RATE_%"])
        ax.axhline(70, linestyle="--")

        st.pyplot(fig)

# =========================
# 📥 DOWNLOAD EXCEL
# =========================
if summary is not None:

    tmp_excel = tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx")
    summary.to_excel(tmp_excel.name, index=False)

    st.download_button(
        label="📥 Download Excel Result",
        data=open(tmp_excel.name, "rb"),
        file_name="container_analysis.xlsx"
    )

# =========================
# 📄 PDF AVEC TABLEAU
# =========================
if summary is not None:

    pdf = FPDF()
    pdf.add_page()

    pdf.set_font("Arial", "B", 10)
    pdf.cell(200, 10, txt=full_title, ln=True, align="C")

    pdf.ln(5)

    # ===== HEADER TABLE =====
    pdf.set_font("Arial", "B", 7)

    col_width = 25

    for col in summary.columns:
        pdf.cell(col_width, 8, col, border=1)

    pdf.ln()

    # ===== TABLE DATA =====
    pdf.set_font("Arial", "", 7)

    for index, row in summary.iterrows():
        for col in summary.columns:
            val = row[col]

            if isinstance(val, float):
                val = round(val, 2)

            pdf.cell(col_width, 8, str(val), border=1)

        pdf.ln()

    # ===== SAVE PDF =====
    tmp_pdf = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    pdf.output(tmp_pdf.name)

    with open(tmp_pdf.name, "rb") as f:
        st.download_button(
            label="📄 Download PDF with Table",
            data=f,
            file_name="container_dashboard.pdf"
        )
