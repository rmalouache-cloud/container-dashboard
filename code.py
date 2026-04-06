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
# SESSION STATE (IMPORTANT)
# =========================

if "packing_type" not in st.session_state:
    st.session_state.packing_type = "Panel"

if "model" not in st.session_state:
    st.session_state.model = ""

if "odf" not in st.session_state:
    st.session_state.odf = ""

# =========================
# LOGOS + HEADER
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
# 🎯 INPUT FIELDS (AJOUTÉS ICI)
# =========================

st.markdown("### 📦 Study Information")

packing_type = st.selectbox(
    "Type of Packing List",
    ["Panel", "SP", "SP/MainBoard", "OC"],
    key="packing_type"
)

model = st.text_input(
    "Model (ex: Mini LED)",
    key="model"
)

odf = st.text_input(
    "ODF (ex: IDL2500)",
    key="odf"
)

st.markdown("---")

# =========================
# 📘 USER GUIDE
# =========================
with st.expander("📘 Manuel d'utilisation / User Guide"):
    st.markdown("...")  # (garde ton texte ici tel quel)

# =========================
# UPLOAD FILE
# =========================

file = st.file_uploader("Upload Packing Excel file", type=["xlsx"])

if file is not None:

    df = pd.read_excel(file)
    df.columns = df.columns.str.strip()

    st.write("📄 Data Preview")
    st.dataframe(df)

    # =========================
    # TITLE DYNAMIQUE PDF (OPTION)
    # =========================
    if st.session_state.model and st.session_state.odf:
        full_title = f"{st.session_state.packing_type} of {st.session_state.model}__{st.session_state.odf}"
        st.success(f"📌 Study Title: {full_title}")

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
        # CALCULATION
        # =========================
        summary["FILL_RATE_%"] = summary["TOTAL_VOLUME"] * 100 / summary["CAPACITY"]

        # =========================
        # STATUS
        # =========================
        summary["STATUS"] = summary["FILL_RATE_%"].apply(
            lambda x: "OK" if x >= 70 else "NON CONFORME"
        )

        # =========================
        # DISPLAY TABLE (FIX)
        # =========================
        st.subheader("📊 Result Table")

        def color_status(val):
            return "background-color: lightgreen" if val == "OK" else "background-color: lightcoral"

        styled = summary.style.map(color_status, subset=["STATUS"])

        st.dataframe(summary)  # ✅ plus stable que st.write(styled)

        # =========================
        # CHART
        # =========================
        st.subheader("📈 Filling Rate Chart")

        fig, ax = plt.subplots(figsize=(7, 3))

        ax.bar(summary["CONTAINER NO"], summary["FILL_RATE_%"])
        ax.axhline(70, linestyle="--", color="red")

        st.pyplot(fig)

        # =========================
        # SUCCESS MESSAGE
        # =========================
        st.success("✅ Analysis completed successfully")
