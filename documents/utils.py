# documents/utils.py
from django.http import HttpResponse

def render_document_to_pdf(html_content, filename):
    """
    Заглушка для генерации PDF (реальная реализация требует дополнительных библиотек)
    """
    return HttpResponse(
        "PDF generation is not implemented yet. Would generate PDF from:\n\n" + html_content,
        content_type='text/plain'
    )