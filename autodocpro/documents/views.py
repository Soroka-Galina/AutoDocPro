# documents/views.py
import json
import logging
import os
import requests
from django.views import View
from django.http import JsonResponse, HttpResponse, HttpResponseBadRequest
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.views.generic import ListView, DetailView
from django.shortcuts import get_object_or_404, render
from django.template import Template, Context
from django.template.loader import render_to_string
from django.conf import settings
from django.contrib import messages
from .models import DocumentTemplate
from .forms import DynamicDocumentForm
from .services import DeepSeekIntegration
from .utils import render_document_to_pdf

logger = logging.getLogger(__name__)

# Контекст для примеров документов
DOCUMENT_CONTEXTS = {
    'motion': {
        'court_name': "Московский городской суд",
        'applicant': {
            'full_name': "Иванов Иван Иванович",
            'address': "г. Москва, ул. Примерная, д. 1",
            'phone': "+7 (999) 123-45-67",
            'email': "ivanov@example.com"
        },
        'motion_type': "отложении судебного заседания",
        'motion_reason': "Необходимость представления дополнительных доказательств",
        'current_date': "20.11.2023",
        'case_number': "А40-12345/2023",
        'judge_name': "Петрова Мария Ивановна"
    },
    'appeal': {
        'appellate_court': "Московский областной суд",
        'appellant': {
            'full_name': "Иванов Иван Иванович",
            'address': "г. Москва, ул. Примерная, д. 1",
            'phone': "+7 (999) 123-45-67",
            'email': "ivanov@example.com"
        },
        'decision_date': "15.10.2023",
        'case_number': "А40-123456/2023",
        'grounds': ["Нарушение норм материального права", "Несоответствие выводов суда"],
        'original_court': "Московский городской суд",
        'original_judge': "Сидоров Алексей Петрович"
    },
    'claim': {
        'court_name': "Московский городской суд",
        'plaintiff': {
            'full_name': "Иванов Иван Иванович",
            'address': "г. Москва, ул. Примерная, д. 1",
            'phone': "+7 (999) 123-45-67",
            'email': "ivanov@example.com",
            'inn': "771234567890"
        },
        'defendant': {
            'full_name': "ООО 'Компания'",
            'address': "г. Москва, ул. Тестовая, д. 2",
            'inn': "770987654321"
        },
        'claim_amount': "115 000 руб.",
        'claim_reason': "долга по договору займа",
        'contract_date': "15.05.2023",
        'contract_number': "123",
        'payment_due_date': "15.08.2023"
    }
}

class DocumentRenderingMixin:
    """Миксин для рендеринга документов"""
    
    def render_template(self, template, context_data=None, format='html'):
        """
        Рендеринг шаблона документа
        :param template: Объект DocumentTemplate
        :param context_data: dict - данные для контекста
        :param format: str - формат вывода (html/pdf)
        :return: str - отрендеренный документ
        """
        try:
            # Проверяем существование файла шаблона
            if not os.path.exists(template.template_file.path):
                raise FileNotFoundError(f"Файл шаблона не найден: {template.template_file.path}")
            
            # Загружаем содержимое шаблона
            with open(template.template_file.path, 'r', encoding='utf-8') as f:
                template_content = f.read()
            
            # Подготавливаем контекст
            context = DOCUMENT_CONTEXTS.get(template.doc_type, {}).copy()
            if context_data:
                context.update(context_data)
            
            # Добавляем общие поля
            context.update({
                'current_date': "20.11.2023",  # Фиксированная дата для примера
            })
            
            # Рендерим шаблон
            rendered_doc = Template(template_content).render(Context(context))
            
            if format == 'pdf':
                return render_document_to_pdf(rendered_doc, template.name)
            return rendered_doc
            
        except Exception as e:
            logger.error(f"Ошибка рендеринга шаблона {template.id}: {str(e)}", exc_info=True)
            raise

    def get_example_context(self, doc_type):
        """Получение контекста для примера документа"""
        return DOCUMENT_CONTEXTS.get(doc_type, {})

def document_preview(request, pk):
    """AJAX-представление для предпросмотра документа"""
    if request.method != 'POST':
        return JsonResponse(
            {'status': 'error', 'message': 'Метод не разрешен'}, 
            status=405
        )

    template = get_object_or_404(DocumentTemplate, pk=pk)
    
    try:
        # Рендерим документ с предоставленными данными
        rendered_doc = DocumentRenderingMixin().render_template(
            template, 
            context_data=request.POST.dict()
        )
        
        # Формируем HTML-ответ с оформлением
        html_response = render_to_string('documents/preview_template.html', {
            'document_content': rendered_doc,
            'template_name': template.name
        })
        
        return HttpResponse(html_response)
        
    except FileNotFoundError:
        logger.error(f"Файл шаблона не найден для документа {pk}")
        return JsonResponse({
            'status': 'error',
            'message': 'Файл шаблона не найден'
        }, status=404)
    except Exception as e:
        logger.error(f"Ошибка рендеринга шаблона: {str(e)}", exc_info=True)
        return JsonResponse({
            'status': 'error',
            'message': f'Ошибка при создании документа: {str(e)}'
        }, status=500)

class DocumentGenerationView(View, DocumentRenderingMixin):
    """View для генерации документов"""
    
    def get(self, request, pk):
        """Отображение формы для генерации документа"""
        template = get_object_or_404(DocumentTemplate, pk=pk)
        form = DynamicDocumentForm(template=template)
        
        # Рендерим пример документа
        try:
            example_context = self.get_example_context(template.doc_type)
            rendered_example = self.render_template(template, example_context)
        except Exception as e:
            rendered_example = f"Ошибка генерации примера: {str(e)}"
            logger.error(f"Ошибка генерации примера: {str(e)}", exc_info=True)
        
        # Обрабатываем dynamic_blocks (может быть строкой JSON или списком)
        dynamic_blocks = template.dynamic_blocks
        if isinstance(dynamic_blocks, str):
            try:
                dynamic_blocks = json.loads(dynamic_blocks)
            except json.JSONDecodeError:
                dynamic_blocks = []
        
        context = {
            'template': template,
            'form': form,
            'rendered_example': rendered_example,
            'example_context': json.dumps(example_context, ensure_ascii=False),
            'dynamic_blocks': dynamic_blocks
        }
        
        return render(request, 'documents/generate_form.html', context)
    
    def post(self, request, pk):
        """Обработка данных формы и генерация документа"""
        template = get_object_or_404(DocumentTemplate, pk=pk)
        form = DynamicDocumentForm(request.POST, template=template)
        
        if not form.is_valid():
            messages.error(request, "Пожалуйста, исправьте ошибки в форме")
            return self.get(request, pk)
        
        try:
            # Собираем данные из динамических блоков
            dynamic_data = {}
            dynamic_blocks = template.dynamic_blocks
            if isinstance(dynamic_blocks, str):
                try:
                    dynamic_blocks = json.loads(dynamic_blocks)
                except json.JSONDecodeError:
                    dynamic_blocks = []
            
            for block in dynamic_blocks:
                block_data = {}
                for field in block.get('fields', []):
                    field_name = f"dynamic_{block['id']}_{field['name']}"
                    block_data[field['name']] = form.cleaned_data.get(field_name)
                dynamic_data[block['id']] = block_data
            
            # Формируем контекст для рендеринга
            context = {
                **form.cleaned_data,
                'dynamic_blocks': dynamic_data
            }
            
            # Генерируем документ
            document_content = self.render_template(template, context)
            
            # Предлагаем варианты действий
            if 'download_pdf' in request.POST:
                pdf_content = self.render_template(template, context, format='pdf')
                response = HttpResponse(pdf_content, content_type='application/pdf')
                response['Content-Disposition'] = f'attachment; filename="{template.slug}.pdf"'
                return response
            
            # По умолчанию показываем HTML-версию
            return render(request, 'documents/generated_document.html', {
                'template': template,
                'document_content': document_content,
                'form_data': context,
                'dynamic_blocks': dynamic_blocks
            })
            
        except Exception as e:
            logger.error(f"Ошибка генерации документа: {str(e)}", exc_info=True)
            messages.error(request, f"Ошибка генерации документа: {str(e)}")
            return self.get(request, pk)

class TemplateDetailView(DetailView, DocumentRenderingMixin):
    """Детальное представление шаблона документа"""
    model = DocumentTemplate
    template_name = 'documents/template_detail.html'
    context_object_name = 'template'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        template = self.object
        
        # Обрабатываем dynamic_blocks (может быть строкой JSON или списком)
        dynamic_blocks = template.dynamic_blocks
        if isinstance(dynamic_blocks, str):
            try:
                dynamic_blocks = json.loads(dynamic_blocks)
            except json.JSONDecodeError:
                dynamic_blocks = []
        
        # Добавляем динамические блоки
        context['dynamic_blocks'] = dynamic_blocks
        
        # Добавляем форму для генерации документа
        context['form'] = DynamicDocumentForm(template=template)
        
        # Генерируем пример документа
        try:
            example_context = self.get_example_context(template.doc_type)
            context['rendered_example'] = self.render_template(template, example_context)
            context['example_context'] = json.dumps(example_context, ensure_ascii=False)
        except Exception as e:
            context['rendered_example'] = f"Ошибка генерации примера: {str(e)}"
            logger.error(f"Ошибка генерации примера для шаблона {template.id}: {str(e)}")
        
        return context

class AIDocumentView(View):
    """Представление для обработки AI-запросов для документов"""
    
    @method_decorator(csrf_exempt)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def post(self, request):
        """Обработка POST-запросов к AI-сервису"""
        logger.info("Получен запрос к AI-сервису")
        
        try:
            data = self._parse_request_data(request)
            action = data.get('action')
            
            if not action:
                logger.error("Отсутствует поле 'action' в запросе")
                return JsonResponse(
                    {'status': 'error', 'message': 'Не указано действие'},
                    status=400
                )

            handlers = {
                'field_help': self._handle_field_help,
                'generate_section': self._handle_generate_section,
                'check_contradictions': self._handle_check_contradictions,
                'analyze_document': self._handle_analyze_document,
                'suggest_improvements': self._handle_suggest_improvements,
                'optimize_appeal': self._handle_optimize_appeal,
                'generate_grounds': self._handle_generate_grounds
            }

            if action not in handlers:
                logger.error(f"Неизвестное действие: {action}")
                return JsonResponse(
                    {'status': 'error', 'message': 'Недопустимое действие'},
                    status=400
                )

            return handlers[action](data)

        except json.JSONDecodeError:
            logger.error("Ошибка декодирования JSON")
            return JsonResponse(
                {'status': 'error', 'message': 'Неверный формат JSON'},
                status=400
            )
        except ValidationError as e:
            logger.error(f"Ошибка валидации: {str(e)}")
            return JsonResponse(
                {'status': 'error', 'message': str(e)},
                status=400
            )
        except ObjectDoesNotExist as e:
            logger.error(f"Объект не найден: {str(e)}")
            return JsonResponse(
                {'status': 'error', 'message': str(e)},
                status=404
            )
        except Exception as e:
            logger.exception("Неожиданная ошибка в AIDocumentView")
            return JsonResponse(
                {
                    'status': 'error', 
                    'message': 'Внутренняя ошибка сервера',
                    'debug': str(e) if settings.DEBUG else None
                },
                status=500
            )

    def _handle_optimize_appeal(self, data):
        """Обработка оптимизации апелляционной жалобы"""
        self._validate_required_fields(data, ['text', 'context'])
        
        try:
            result = DeepSeekIntegration.optimize_text(
                data['text'],
                data['context']
            )
            
            return JsonResponse({
                'status': 'success',
                'optimized_text': result['choices'][0]['message']['content']
            })
            
        except Exception as e:
            logger.error(f"Optimization error: {str(e)}", exc_info=True)
            return JsonResponse({
                'status': 'error',
                'message': 'Ошибка оптимизации текста'
            }, status=500)

    def _handle_generate_grounds(self, data):
        """Генерация оснований для апелляции"""
        self._validate_required_fields(data, ['decision_text', 'case_details'])
        
        prompt = f"""Сгенерируйте юридические основания для апелляции на решение:
{data['decision_text']}

Детали дела:
{data['case_details']}
"""
        try:
            result = DeepSeekIntegration.generate_text(prompt)
            grounds = self._extract_grounds_from_response(result)
            
            return JsonResponse({
                'status': 'success',
                'grounds': grounds
            })
            
        except Exception as e:
            logger.error(f"Grounds generation error: {str(e)}", exc_info=True)
            return JsonResponse({
                'status': 'error',
                'message': 'Ошибка генерации оснований'
            }, status=500)

    def _extract_grounds_from_response(self, response):
        """Извлечение структурированных оснований из ответа AI"""
        # Здесь можно добавить парсинг ответа для структурированного вывода
        return response['choices'][0]['message']['content']

    def _handle_field_help(self, data):
        """Обработка запроса справки по полю документа"""
        logger.info("Обработка запроса справки по полю")
        
        self._validate_required_fields(data, ['field', 'template_id'])
        
        template = self._get_template(data['template_id'])
        field_meta = self._get_field_metadata(template, data['field'])
        
        try:
            result = DeepSeekIntegration.get_field_help(
                template=template,
                field_meta=field_meta,
                current_value=data.get('value', ''),
                user_context=data.get('context', {})
            )
            
            return JsonResponse({
                'status': 'success',
                'help_text': result.get('help_text', ''),
                'examples': result.get('examples', []),
                'common_mistakes': result.get('common_mistakes', []),
                'legal_references': result.get('legal_references', [])
            })
            
        except requests.exceptions.HTTPError as e:
            status_code = e.response.status_code
            error_msg = self._get_api_error_message(e)
            logger.error(f"Ошибка API при запросе справки: {error_msg}")
            return JsonResponse(
                {
                    'status': 'error',
                    'message': f'Ошибка API: {error_msg}',
                    'api_status_code': status_code
                },
                status=502 if status_code >= 500 else 400
            )
        except Exception as e:
            logger.error(f"Ошибка при запросе справки: {str(e)}", exc_info=True)
            return JsonResponse(
                {
                    'status': 'error',
                    'message': 'Не удалось получить справку по полю'
                },
                status=500
            )

    def _parse_request_data(self, request):
        """Парсинг данных запроса с обработкой ошибок"""
        if request.content_type == 'application/json':
            try:
                return json.loads(request.body.decode('utf-8'))
            except json.JSONDecodeError as e:
                logger.error(f"Ошибка декодирования JSON: {str(e)}")
                raise
        return request.POST.dict()

    def _validate_required_fields(self, data, required_fields):
        """Проверка наличия обязательных полей"""
        missing_fields = [f for f in required_fields if f not in data]
        if missing_fields:
            error_msg = f"Отсутствуют обязательные поля: {', '.join(missing_fields)}"
            logger.error(error_msg)
            raise ValidationError(error_msg)

    def _get_template(self, template_id):
        """Получение шаблона документа с обработкой ошибок"""
        try:
            return DocumentTemplate.objects.get(pk=template_id)
        except (ValueError, ObjectDoesNotExist) as e:
            error_msg = f"Шаблон с ID {template_id} не найден"
            logger.error(error_msg)
            raise ObjectDoesNotExist(error_msg)

    def _get_field_metadata(self, template, field_name):
        """Получение метаданных поля с обработкой ошибок"""
        if not hasattr(template, 'fields_schema'):
            error_msg = "Шаблон не содержит схемы полей"
            logger.error(error_msg)
            raise ValidationError(error_msg)
            
        field_meta = next(
            (f for f in template.fields_schema.get('fields', []) 
             if f['name'] == field_name), 
            None
        )
        
        if not field_meta:
            error_msg = f"Поле '{field_name}' не найдено в шаблоне"
            logger.error(error_msg)
            raise ValidationError(error_msg)
        
        return field_meta

    def _get_api_error_message(self, http_error):
        """Формирование понятного сообщения об ошибке API"""
        try:
            error_data = http_error.response.json()
            return error_data.get('error', {}).get('message', str(http_error))
        except:
            return str(http_error)

class HomeView(ListView):
    """Главная страница с популярными шаблонами"""
    model = DocumentTemplate
    template_name = "documents/home.html"
    context_object_name = "templates"
    queryset = DocumentTemplate.objects.filter(is_active=True).order_by('name')[:6]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['document_categories'] = DocumentTemplate.LEGAL_CATEGORIES
        return context

def motion_template(request):
    """View для шаблона ходатайства"""
    template = get_object_or_404(DocumentTemplate, doc_type='motion')
    
    # Обрабатываем dynamic_blocks (может быть строкой JSON или списком)
    dynamic_blocks = template.dynamic_blocks
    if isinstance(dynamic_blocks, str):
        try:
            dynamic_blocks = json.loads(dynamic_blocks)
        except json.JSONDecodeError:
            dynamic_blocks = []
    
    context = {
        'template': template,
        'form': DynamicDocumentForm(template=template),
        'dynamic_blocks': dynamic_blocks
    }
    return render(request, 'documents/motion_form.html', context)

def appeal_template(request):
    """View для шаблона апелляционной жалобы"""
    template = get_object_or_404(DocumentTemplate, doc_type='appeal')
    
    # Обрабатываем dynamic_blocks (может быть строкой JSON или списком)
    dynamic_blocks = template.dynamic_blocks
    if isinstance(dynamic_blocks, str):
        try:
            dynamic_blocks = json.loads(dynamic_blocks)
        except json.JSONDecodeError:
            dynamic_blocks = []
    
    context = {
        'template': template,
        'form': DynamicDocumentForm(template=template),
        'dynamic_blocks': dynamic_blocks
    }
    return render(request, 'documents/appeal_form.html', context)

def claim_template(request):
    """View для шаблона искового заявления"""
    template = get_object_or_404(DocumentTemplate, doc_type='claim')
    
    # Обрабатываем dynamic_blocks (может быть строкой JSON или списком)
    dynamic_blocks = template.dynamic_blocks
    if isinstance(dynamic_blocks, str):
        try:
            dynamic_blocks = json.loads(dynamic_blocks)
        except json.JSONDecodeError:
            dynamic_blocks = []
    
    context = {
        'template': template,
        'form': DynamicDocumentForm(template=template),
        'dynamic_blocks': dynamic_blocks
    }
    return render(request, 'documents/claim_form.html', context)

class TemplateListView(ListView):
    """Список шаблонов документов"""
    model = DocumentTemplate
    template_name = "documents/template_list.html"
    context_object_name = "templates"
    paginate_by = 12

    def get_queryset(self):
        queryset = super().get_queryset().filter(is_active=True)
        
        # Фильтрация по категории
        category = self.request.GET.get('category')
        if category:
            queryset = queryset.filter(category=category)
        
        # Фильтрация по типу документа
        doc_type = self.request.GET.get('type')
        if doc_type:
            queryset = queryset.filter(doc_type=doc_type)
        
        # Поиск
        search_query = self.request.GET.get('q')
        if search_query:
            queryset = queryset.filter(name__icontains=search_query)
        
        return queryset.order_by('name')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'ai_integration': True,
            'category_filter': self.request.GET.get('category', ''),
            'type_filter': self.request.GET.get('type', ''),
            'search_query': self.request.GET.get('q', '')
        })
        return context

def download_document(request):
    """Скачивание готового документа (обрабатывает POST с данными документа)"""
    if request.method != 'POST':
        return JsonResponse(
            {'status': 'error', 'message': 'Метод не разрешен'}, 
            status=405
        )
    
    try:
        template_id = request.POST.get('template_id')
        template = get_object_or_404(DocumentTemplate, pk=template_id)
        
        # Рендерим документ в PDF
        pdf_content = DocumentRenderingMixin().render_template(
            template,
            context_data=request.POST.dict(),
            format='pdf'
        )
        
        response = HttpResponse(pdf_content, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{template.slug}.pdf"'
        return response
        
    except Exception as e:
        logger.error(f"Ошибка генерации PDF: {str(e)}", exc_info=True)
        return JsonResponse({
            'status': 'error',
            'message': f'Ошибка при создании PDF: {str(e)}'
        }, status=500)