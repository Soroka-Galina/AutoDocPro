# autodocpro/urls.py
from django.contrib import admin
from django.urls import path, include
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.conf import settings
from django.conf.urls.static import static
from documents.views import (
    HomeView,
    TemplateListView,
    TemplateDetailView,
    download_document,
    document_preview,
    AIDocumentView,
    motion_template,
    appeal_template,
    claim_template
)

# Основные URL-паттерны
urlpatterns = [
    path('admin/', admin.site.urls),
    path('', HomeView.as_view(), name='home'),
    
    # Группировка URL для шаблонов документов
    path('templates/', include([
        path('', TemplateListView.as_view(), name='template_list'),
        path('<int:pk>/', TemplateDetailView.as_view(), name='template_detail'),
        path('<int:pk>/preview/', document_preview, name='document_preview'),
        
        # Популярные шаблоны (можно вынести в отдельный файл при росте количества)
        path('motion/', motion_template, name='motion_template'),
        path('appeal/', appeal_template, name='appeal_template'),
        path('claim/', claim_template, name='claim_template'),
    ])),
    
    # API endpoints
    path('api/', include([
        path('ai/', AIDocumentView.as_view(), name='ai_api'),
        # Можно добавить другие API endpoints здесь
    ])),
    
    path('download/<int:doc_id>/', download_document, name='download_document'),
]

# Обслуживание статических файлов в разработке
if settings.DEBUG:
    urlpatterns += staticfiles_urlpatterns()
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    
    # Добавляем debug toolbar
    if 'debug_toolbar' in settings.INSTALLED_APPS:
        import debug_toolbar
        urlpatterns = [
            path('__debug__/', include(debug_toolbar.urls)),
        ] + urlpatterns