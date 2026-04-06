import io

# =========================
# PDF
# =========================
if "summary" in locals() and summary is not None:

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

    # ✅ Utilisation d'un buffer mémoire (évite les None)
    pdf_bytes = pdf.output(dest="S").encode("latin1")

    st.download_button(
        label="📄 Download PDF",
        data=pdf_bytes,
        file_name=f"{model}_{odf}_dashboard.pdf",
        mime="application/pdf"
    )
