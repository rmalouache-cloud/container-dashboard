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
container_logo = Image.open("conteneur_logo.png")
stream_logo = Image.open("stream_logo.png")

col1, col2, col3 = st.columns([1, 5, 1])

with col1:
    st.image(container_logo, width=400)

with col2:
    st.title("Container Filling Industrial Dashboard")
    st.caption("Supply Chain Analysis - BOM & Packing Control")

with col3:
    st.image(stream_logo, width=800)

# =========================
# INPUT FIELDS (IMPORTANT)
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
    # DETECT CBM
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
        # GROUP
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

        fig, ax = plt.subplots(figsize=(7, 3))
        ax.bar(summary["CONTAINER NO"], summary["FILL_RATE_%"])
        ax.axhline(70, linestyle="--")

        st.pyplot(fig)

# =========================
# DOWNLOAD EXCEL (TOUJOURS VISIBLE)
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
# PDF EXPORT (OPTIONNEL)
# =========================
if summary is not None:

    tmp_img = tempfile.NamedTemporaryFile(delete=False, suffix=".png").name
    fig.savefig(tmp_img, bbox_inches="tight")

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 12)

    pdf.cell(200, 10, txt=full_title, ln=True, align="C")

    pdf.ln(5)

    pdf.image(tmp_img, w=180)

    pdf_file = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    pdf.output(pdf_file.name)

    with open(pdf_file.name, "rb") as f:
        st.download_button(
            label="📄 Download PDF",
            data=f,
            file_name="container_dashboard.pdf"
        )
