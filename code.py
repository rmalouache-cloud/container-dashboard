import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
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
# INPUTS
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
# TITLE
# =========================
if model and odf:
    full_title = f"Container Filling Industrial Dashboard of {packing_type} of {model}__{odf}"
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
    # CBM COLUMN
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

        # =========================
        # COLOR TABLE STREAMLIT
        # =========================
        def highlight_status(val):
            if val == "OK":
                return "background-color: lightgreen"
            elif val == "NON CONFORME":
                return "background-color: lightcoral"
            return ""

        styled_df = summary.style.applymap(
            highlight_status
        )

        st.subheader("📊 Result Table")
        st.dataframe(styled_df)

        # =========================
        # CHART
        # =========================
        st.subheader("📈 Filling Rate Chart")

        fig, ax = plt.subplots()
        ax.bar(summary["CONTAINER NO"], summary["FILL_RATE_%"])
        ax.axhline(70, linestyle="--")

        st.pyplot(fig)

# =========================
# EXCEL DOWNLOAD
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
# PDF GENERATION
# =========================
if summary is not None:

    pdf = FPDF(orientation="L", unit="mm", format="A4")
    pdf.add_page()

    # ===== LOGO =====
    logo_path = "logo.png"  # 🔴 change ici

    try:
        pdf.image(logo_path, x=10, y=8, w=30)
    except:
        pass

    # ===== TITLE =====
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, full_title, ln=True, align="C")

    pdf.ln(10)

    # =========================
    # TABLE HEADER
    # =========================
    pdf.set_font("Arial", "B", 8)

    page_width = 270
    col_width = page_width / len(summary.columns)

    for col in summary.columns:
        pdf.cell(col_width, 8, str(col), border=1, align="C")

    pdf.ln()

    # =========================
    # TABLE CONTENT (COLOR STATUS)
    # =========================
    pdf.set_font("Arial", "", 8)

    for _, row in summary.iterrows():
        for col in summary.columns:
            val = row[col]

            if isinstance(val, float):
                val = f"{val:.2f}"

            # COLOR STATUS
            if col == "STATUS":
                if val == "OK":
                    pdf.set_text_color(0, 128, 0)  # green
                else:
                    pdf.set_text_color(255, 0, 0)  # red
            else:
                pdf.set_text_color(0, 0, 0)

            pdf.cell(col_width, 8, str(val), border=1, align="C")

        pdf.ln()

    pdf.ln(5)

    # =========================
    # ADD CHART IMAGE
    # =========================
    tmp_img = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
    fig.savefig(tmp_img.name)

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
