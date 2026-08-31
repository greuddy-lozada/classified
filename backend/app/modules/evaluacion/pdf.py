from fpdf import FPDF

from app.schemas.evaluacion import BoletinOut


def _t(value: str) -> str:
    return value.encode("latin-1", "replace").decode("latin-1")


def render_boletin_pdf(data: BoletinOut) -> bytes:
    pdf = FPDF()
    pdf.set_compression(False)
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 14)
    titulo = "Informe descriptivo" if data.esquema == "informe" else "Boletin de calificaciones"
    pdf.cell(0, 10, _t(titulo), new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", size=12)
    pdf.cell(0, 8, _t(f"{data.alumno_nombres} {data.alumno_apellidos}"), new_x="LMARGIN", new_y="NEXT")
    if data.promedio_final is not None:
        extra = " (reparacion)" if data.necesita_reparacion else ""
        pdf.cell(0, 8, _t(f"Promedio final: {data.promedio_final}{extra}"), new_x="LMARGIN", new_y="NEXT")
    for lapso in data.lapsos:
        pdf.set_font("Helvetica", "B", 12)
        cierre = " cerrado" if lapso.cerrado else ""
        promedio = f"  promedio {lapso.promedio}" if lapso.promedio is not None else ""
        pdf.cell(0, 8, _t(f"{lapso.lapso_nombre}{cierre}{promedio}"), new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Helvetica", size=11)
        for nota in lapso.notas:
            pdf.cell(0, 7, _t(f"{nota.materia_nombre}: {nota.valor}"), new_x="LMARGIN", new_y="NEXT")
        for item in lapso.informes:
            linea = f"{item.area}: {item.juicio}"
            if item.comentario:
                linea += f" — {item.comentario}"
            pdf.cell(0, 7, _t(linea), new_x="LMARGIN", new_y="NEXT")
    return bytes(pdf.output())
