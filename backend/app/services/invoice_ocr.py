"""
OCR Service for invoice text recognition
Uses Tesseract OCR to extract text from PDF and images
"""
import pytesseract
from pdf2image import convert_from_path
from PIL import Image
import io
from typing import Union
from pathlib import Path
from loguru import logger
from app.core.config import settings


class InvoiceOCRService:
    """Сервис распознавания текста из PDF и изображений счетов"""

    def __init__(self):
        # Настройка pytesseract для русского языка
        self.tesseract_config = f'--oem 3 --psm 6 -l {settings.OCR_LANGUAGE}'
        self.dpi = settings.OCR_DPI

    def extract_text_from_pdf(self, pdf_path: Union[str, Path]) -> str:
        """
        Извлечение текста из PDF
        Сначала пробует извлечь текстовый слой, если не получается - использует OCR
        """
        try:
            # Сначала пробуем извлечь текстовый слой
            import pypdf
            with open(pdf_path, 'rb') as file:
                pdf_reader = pypdf.PdfReader(file)
                text = ""
                for page in pdf_reader.pages:
                    text += page.extract_text()

                # Если текст извлечен успешно (не пустой и не мусор)
                if len(text.strip()) > 100:
                    logger.info(f"Текст извлечен из PDF напрямую: {len(text)} символов")
                    return text

            # Если текста нет - используем OCR
            logger.info("Текстовый слой не найден, используем OCR")
            return self._ocr_from_pdf(pdf_path)

        except Exception as e:
            logger.error(f"Ошибка при извлечении текста из PDF: {e}")
            # Fallback на OCR
            return self._ocr_from_pdf(pdf_path)

    def _ocr_from_pdf(self, pdf_path: Union[str, Path]) -> str:
        """OCR распознавание PDF"""
        try:
            # Конвертируем PDF в изображения
            images = convert_from_path(pdf_path, dpi=self.dpi)

            text = ""
            for i, image in enumerate(images):
                logger.info(f"Обработка страницы {i+1}/{len(images)}")
                page_text = pytesseract.image_to_string(
                    image,
                    config=self.tesseract_config
                )
                text += page_text + "\n\n"

            logger.info(f"OCR завершен: {len(text)} символов")
            return text

        except Exception as e:
            logger.error(f"Ошибка OCR для PDF: {e}")
            raise

    def extract_text_from_image(self, image_path: Union[str, Path]) -> str:
        """Извлечение текста из изображения"""
        try:
            image = Image.open(image_path)
            text = pytesseract.image_to_string(
                image,
                config=self.tesseract_config
            )
            logger.info(f"Текст извлечен из изображения: {len(text)} символов")
            return text

        except Exception as e:
            logger.error(f"Ошибка при OCR изображения: {e}")
            raise

    def process_file(self, file_path: Union[str, Path]) -> str:
        """
        Универсальный метод обработки файла
        Автоматически определяет формат и использует соответствующий метод
        """
        file_path = Path(file_path)
        extension = file_path.suffix.lower()

        logger.info(f"Начинаю OCR обработку файла: {file_path.name}")

        if extension == '.pdf':
            return self.extract_text_from_pdf(file_path)
        elif extension in ['.jpg', '.jpeg', '.png', '.tiff', '.bmp']:
            return self.extract_text_from_image(file_path)
        else:
            raise ValueError(f"Неподдерживаемый формат файла: {extension}")
