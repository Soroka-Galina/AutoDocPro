// static/js/dynamic-blocks.js

class DynamicBlocksValidator {
    static validateBlockStructure(block) {
        const requiredFields = ['id', 'title', 'fields'];
        const fieldProps = ['name', 'type', 'label'];
        
        // Проверка обязательных полей блока
        if (!requiredFields.every(field => field in block)) {
            throw new Error(`Block is missing required fields: ${requiredFields.join(', ')}`);
        }

        // Валидация каждого поля
        block.fields.forEach(field => {
            if (!fieldProps.every(prop => prop in field)) {
                throw new Error(`Field is missing required properties: ${fieldProps.join(', ')}`);
            }

            // Дополнительная валидация типов
            const validTypes = ['text', 'select', 'textarea', 'checkbox'];
            if (!validTypes.includes(field.type)) {
                throw new Error(`Invalid field type: ${field.type}. Must be one of: ${validTypes.join(', ')}`);
            }

            // Валидация опций для select
            if (field.type === 'select' && (!field.options || !Array.isArray(field.options))) {
                throw new Error('Select field must have options array');
            }
        });

        // Валидация зависимостей
        if (block.dependencies) {
            this.validateDependencies(block.dependencies);
        }
    }

    static validateDependencies(dependencies) {
        const validConditions = ['equals', 'not_equals', 'contains', 'greater_than', 'less_than'];
        
        Object.entries(dependencies).forEach(([target, conditions]) => {
            if (!Array.isArray(conditions)) {
                throw new Error(`Dependencies for ${target} must be an array`);
            }

            conditions.forEach(cond => {
                if (!validConditions.includes(cond.condition)) {
                    throw new Error(`Invalid condition: ${cond.condition}`);
                }
            });
        });
    }
}

// Интеграция с существующим кодом
document.addEventListener('DOMContentLoaded', function() {
    try {
        // Получаем данные динамических блоков из DOM
        const blocksData = JSON.parse(document.getElementById('dynamic-blocks-data').textContent);
        
        // Валидация всех блоков
        blocksData.forEach(block => {
            DynamicBlocksValidator.validateBlockStructure(block);
        });

        // Инициализация только после успешной валидации
        initDynamicBlocks();
        
    } catch (error) {
        console.error('Dynamic blocks validation failed:', error);
        showErrorToUser('Ошибка в структуре динамических блоков');
        // Можно отключить функциональность или показать fallback-интерфейс
    }
});

function showErrorToUser(message) {
    const errorContainer = document.createElement('div');
    errorContainer.className = 'alert alert-danger';
    errorContainer.textContent = message;
    document.body.prepend(errorContainer);
}