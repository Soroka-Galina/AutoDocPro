import json
import os
from django.db import models
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
import jsonschema

User = get_user_model()


class AIRequestHistory(models.Model):
    """
    Модель для хранения истории запросов к AI-сервисам
    """
    REQUEST_TYPES = [
        ('field_help', 'Помощь по полю'),
        ('generate', 'Генерация текста'),
        ('analysis', 'Анализ документа'),
        ('other', 'Другое')
    ]
    
    user = models.ForeignKey(
        User, 
        null=True, 
        on_delete=models.SET_NULL,
        verbose_name='Пользователь'
    )
    request_type = models.CharField(
        max_length=20, 
        choices=REQUEST_TYPES,
        verbose_name='Тип запроса'
    )
    request_data = models.JSONField(
        encoder=json.JSONEncoder,
        verbose_name='Данные запроса'
    )
    response_data = models.JSONField(
        encoder=json.JSONEncoder,
        verbose_name='Данные ответа'
    )
    is_error = models.BooleanField(
        default=False,
        verbose_name='Ошибка'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата создания'
    )
    processing_time = models.FloatField(
        null=True,
        verbose_name='Время обработки (сек)'
    )
    api_endpoint = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name='API Endpoint'
    )
    model_used = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name='Использованная модель'
    )
    
    class Meta:
        verbose_name = 'История запроса AI'
        verbose_name_plural = 'История запросов AI'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.get_request_type_display()} - {self.created_at}"


# Схема для валидации dynamic_blocks
DYNAMIC_BLOCKS_SCHEMA = {
    "type": "array",
    "items": {
        "type": "object",
        "properties": {
            "id": {"type": "string"},
            "title": {"type": "string"},
            "template": {"type": "string"},
            "default_visible": {"type": "boolean"},
            "fields": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "type": {"type": "string", "enum": ["text", "select", "textarea", "checkbox"]},
                        "label": {"type": "string"},
                        "required": {"type": "boolean"},
                        "options": {"type": "array", "items": {"type": "string"}},
                        "controls": {"type": "array", "items": {"type": "string"}}
                    },
                    "required": ["name", "type", "label"]
                }
            }
        },
        "required": ["id", "title", "fields"]
    }
}


def validate_dynamic_blocks(value):
    """Валидация структуры dynamic_blocks по JSON схеме"""
    try:
        jsonschema.validate(value, DYNAMIC_BLOCKS_SCHEMA)
    except jsonschema.ValidationError as e:
        raise ValidationError(f"Invalid dynamic_blocks structure: {e.message}")


class DocumentTemplate(models.Model):
    """
    Модель шаблона документа с полями и настройками генерации
    """
    DOC_TYPES = [
        ('claim', 'Исковое заявление'),
        ('motion', 'Ходатайство'),
        ('appeal', 'Апелляционная жалоба'),
    ]
    
    LEGAL_CATEGORIES = [
        ('civil', 'Гражданские дела'),
        ('arbitration', 'Арбитражные споры'),
        ('administrative', 'Административные дела'),
        ('criminal', 'Уголовные дела'),
        ('family', 'Семейные дела'),
        ('labor', 'Трудовые споры'),
        ('tax', 'Налоговые споры'),
        ('corporate', 'Корпоративные споры'),
    ]
    
    name = models.CharField(
        max_length=255, 
        verbose_name="Название шаблона"
    )
    doc_type = models.CharField(
        max_length=50, 
        choices=DOC_TYPES, 
        verbose_name="Тип документа"
    )
    category = models.CharField(
        max_length=50,
        choices=LEGAL_CATEGORIES,
        default='civil',
        verbose_name="Категория дела"
    )
    description = models.TextField(
        verbose_name="Описание"
    )
    template_file = models.FileField(
        upload_to='templates/', 
        verbose_name="Файл шаблона"
    )
    fields_schema = models.JSONField(
        default=dict,
        encoder=json.JSONEncoder,
        decoder=json.JSONDecoder,
        verbose_name="Схема полей"
    )
    dynamic_blocks = models.JSONField(
        default=list,
        validators=[validate_dynamic_blocks],
        help_text="JSON структура динамических блоков и их зависимостей",
        verbose_name="Динамические блоки"
    )
    is_active = models.BooleanField(
        default=True, 
        verbose_name="Активный"
    )
    ai_enhancement = models.BooleanField(
        default=False, 
        verbose_name="AI улучшение"
    )
    ai_max_length = models.PositiveIntegerField(
        default=2000, 
        verbose_name="Макс. длина AI"
    )

    class Meta:
        verbose_name = "Шаблон документа"
        verbose_name_plural = "Шаблоны документов"
        ordering = ['name']

    def __str__(self):
        return self.name

    def clean(self):
        """Валидация JSON данных в fields_schema и dynamic_blocks"""
        if isinstance(self.fields_schema, str):
            try:
                self.fields_schema = json.loads(self.fields_schema)
            except json.JSONDecodeError:
                raise ValidationError("Invalid JSON in fields_schema")
        
        if isinstance(self.dynamic_blocks, str):
            try:
                self.dynamic_blocks = json.loads(self.dynamic_blocks)
            except json.JSONDecodeError:
                raise ValidationError("Invalid JSON in dynamic_blocks")

    def get_template_path(self):
        """Возвращает абсолютный путь к файлу шаблона"""
        if self.template_file:
            return os.path.abspath(self.template_file.path)
        return None


class GeneratedDocument(models.Model):
    """
    Модель сгенерированного документа с привязкой к шаблону
    """
    template = models.ForeignKey(
        DocumentTemplate, 
        on_delete=models.CASCADE, 
        verbose_name="Шаблон"
    )
    content = models.JSONField(
        verbose_name="Данные документа"
    )
    document_content = models.TextField(
        null=True, 
        blank=True, 
        verbose_name="Содержимое документа"
    )
    file = models.FileField(
        upload_to='generated/', 
        null=True, 
        blank=True, 
        verbose_name="Файл"
    )
    created_at = models.DateTimeField(
        auto_now_add=True, 
        verbose_name="Дата создания"
    )
    session_key = models.CharField(
        max_length=40, 
        verbose_name="Ключ сессии"
    )

    class Meta:
        verbose_name = "Сгенерированный документ"
        verbose_name_plural = "Сгенерированные документы"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.template.name} - {self.created_at}"

    def get_file_path(self):
        """Возвращает абсолютный путь к сгенерированному файлу"""
        if self.file:
            return os.path.abspath(self.file.path)
        return None