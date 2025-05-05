# personal_comparator/utils/helpers.py

from fpdf import FPDF

class PDF(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 14)
        self.cell(0, 10, 'Relatório de Análise de Exercício', 0, 1, 'C')
        self.ln(10)

    def chapter_title(self, title):
        self.set_font('Arial', 'B', 12)
        self.cell(0, 10, title, 0, 1, 'L')
        self.ln(4)

    def chapter_body(self, body):
        self.set_font('Arial', '', 12)
        self.multi_cell(0, 10, body)
        self.ln()

def generate_pdf_report(student_name, insights, avg_error, full_feedback=None):
    pdf = PDF()
    pdf.add_page()

    pdf.chapter_title(f"Aluno: {student_name}")
    pdf.chapter_body(f"Erro médio total: {avg_error:.2f}°\n\n")

    pdf.chapter_title("Principais Correções:")
    for insight in insights[:5]:
        pdf.chapter_body(f"- {insight}")

    if full_feedback:
        pdf.chapter_title("Feedback Inteligente Personalizado:")
        pdf.chapter_body(full_feedback)

    # Gera PDF em memória
    pdf_output = pdf.output(dest='S').encode('latin1')  # 'S' = string, latin1 é necessário
    return pdf_output

