# documents/forms.py
from django import forms
from django.utils.safestring import mark_safe
import json

class DynamicDocumentForm(forms.Form):
    def __init__(self, *args, **kwargs):
        self.template = kwargs.pop('template')
        super().__init__(*args, **kwargs)
        self._build_form_fields()

    def _build_form_fields(self):
        """Создает поля формы на основе схемы шаблона"""
        # Обработка fields_schema (может быть строкой или словарем)
        if isinstance(self.template.fields_schema, str):
            try:
                fields_schema = json.loads(self.template.fields_schema)
            except json.JSONDecodeError:
                fields_schema = {'fields': []}
        else:
            fields_schema = self.template.fields_schema
            
        # Обычные поля
        for field in fields_schema.get('fields', []):
            self._add_form_field(field)
        
        # Динамические блоки
        if hasattr(self.template, 'dynamic_blocks'):
            dynamic_blocks = self.template.dynamic_blocks
            if isinstance(dynamic_blocks, str):
                try:
                    dynamic_blocks = json.loads(dynamic_blocks)
                except json.JSONDecodeError:
                    dynamic_blocks = []
            
            for block in dynamic_blocks:
                for field in block.get('fields', []):
                    field_name = f"dynamic_{block['id']}_{field['name']}"
                    self._add_form_field({
                        **field,
                        'name': field_name,
                        'label': f"{block['title']} - {field['label']}"
                    })

    def _add_form_field(self, field_config):
        """Добавляет одно поле в форму"""
        field_name = field_config['name']
        field_type = field_config.get('type', 'text')
        
        field_params = {
            'label': field_config.get('label', field_name),
            'required': field_config.get('required', True),
            'help_text': field_config.get('description', ''),
            'initial': field_config.get('default', '')
        }

        # Определяем виджет в зависимости от типа поля
        if field_type == 'textarea':
            field_params['widget'] = forms.Textarea(attrs={'rows': 3, 'class': 'form-control'})
        elif field_type == 'select':
            choices = [(opt, opt) for opt in field_config.get('options', [])]
            field_params['widget'] = forms.Select(choices=choices, attrs={'class': 'form-select'})
        else:
            field_params['widget'] = forms.TextInput(attrs={'class': 'form-control'})
        
        self.fields[field_name] = forms.CharField(**field_params)
        
        if hasattr(self.template, 'ai_enhancement') and self.template.ai_enhancement:
            self._add_ai_button(field_name)

    def _add_ai_button(self, field_name):
        """Добавляет кнопку AI-помощи к полю"""
        help_text = self.fields[field_name].help_text or ''
        ai_button = (
            '<div class="mt-2">'
            '<button type="button" class="btn btn-sm btn-outline-primary btn-ai-help" '
            f'data-field="{field_name}" data-bs-toggle="tooltip" title="Заполнить с помощью AI">'
            '<i class="bi bi-magic"></i> AI помощь'
            '</button>'
            '</div>'
        )
        self.fields[field_name].help_text = mark_safe(f"{help_text}{ai_button}")