import os
import PyPDF2
from docx import Document
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile


def extract_text_from_pdf(file_path):
    """Извлекает текст из PDF файла"""
    try:
        with open(file_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
        return text.strip()
    except Exception as e:
        raise Exception(f"Ошибка при чтении PDF: {str(e)}")


def extract_text_from_docx(file_path):
    """Извлекает текст из Word документа"""
    try:
        doc = Document(file_path)
        text = ""
        for paragraph in doc.paragraphs:
            text += paragraph.text + "\n"
        return text.strip()
    except Exception as e:
        raise Exception(f"Ошибка при чтении Word документа: {str(e)}")


def process_uploaded_file(uploaded_file):
    """Обрабатывает загруженный файл и извлекает текст"""
    # Сохраняем файл временно
    file_name = uploaded_file.name
    file_extension = os.path.splitext(file_name)[1].lower()
    
    # Создаем временный файл
    temp_path = default_storage.save(f'temp/{file_name}', ContentFile(uploaded_file.read()))
    full_path = default_storage.path(temp_path)
    
    try:
        # Извлекаем текст в зависимости от типа файла
        if file_extension == '.pdf':
            text = extract_text_from_pdf(full_path)
        elif file_extension in ['.docx', '.doc']:
            text = extract_text_from_docx(full_path)
        else:
            raise Exception("Неподдерживаемый формат файла. Поддерживаются только PDF и Word документы.")
        
        # Очищаем временный файл
        default_storage.delete(temp_path)
        
        return text
    
    except Exception as e:
        # Удаляем временный файл в случае ошибки
        if default_storage.exists(temp_path):
            default_storage.delete(temp_path)
        raise e


def clean_text_for_ai(text, max_length=8000):
    """Очищает и обрезает текст для отправки в AI"""
    # Удаляем лишние пробелы и переносы строк
    text = ' '.join(text.split())
    
    # Обрезаем текст если он слишком длинный
    if len(text) > max_length:
        text = text[:max_length] + "..."
    
    return text
