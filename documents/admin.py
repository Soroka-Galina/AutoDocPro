from django.contrib import admin
from .models import DocumentTemplate
import json

def prefill_schema(modeladmin, request, queryset):
    for template in queryset:
        if not template.fields_schema:
            template.fields_schema = template.generate_fields_schema()
            template.save()
prefill_schema.short_description = "Автозаполнить fields_schema"

class DocumentTemplateAdmin(admin.ModelAdmin):
    list_display = ('name', 'doc_type', 'is_active')
    list_filter = ('doc_type', 'is_active')
    search_fields = ('name', 'description')
    actions = [prefill_schema]

admin.site.register(DocumentTemplate, DocumentTemplateAdmin)