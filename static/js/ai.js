// documents/static/js/ai.js
class AIDocumentAssistant {
    constructor() {
        this.initEventListeners();
        this.initDynamicBlocks();
    }

    // Инициализация основных обработчиков событий
    initEventListeners() {
        // AI чат
        document.getElementById('ai-send-btn')?.addEventListener('click', () => this.sendAIQuestion());
        document.getElementById('ai-question-input')?.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') this.sendAIQuestion();
        });

        // Контекстные подсказки
        document.querySelectorAll('.form-control').forEach(field => {
            field.addEventListener('focus', () => {
                this.fetchContextualAdvice(field.name);
            });
        });
    }

    // Работа с AI чатом
    async sendAIQuestion() {
        const input = document.getElementById('ai-question-input');
        const message = input.value.trim();
        if (!message) return;

        const chatBox = document.getElementById('ai-chat-messages');
        this.addChatMessage('user', message);
        input.value = '';
        
        this.showLoadingIndicator();
        
        try {
            const response = await fetch("/api/ai/", {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
                },
                body: JSON.stringify({
                    action: 'chat_question',
                    question: message,
                    context: this.getCurrentDocumentContext()
                })
            });
            
            const data = await response.json();
            this.removeLoadingIndicator();
            
            if (data.status === 'success') {
                this.addChatMessage('ai', data.answer);
            } else {
                this.addChatMessage('error', data.message || 'Произошла ошибка');
            }
        } catch (error) {
            this.removeLoadingIndicator();
            this.addChatMessage('error', 'Ошибка соединения с сервером');
        }
    }

    addChatMessage(role, content) {
        const chatBox = document.getElementById('ai-chat-messages');
        const messageClass = {
            user: 'user-message',
            ai: 'ai-message',
            error: 'ai-error'
        }[role] || '';
        
        chatBox.innerHTML += `
            <div class="message ${messageClass}">
                <strong>${role === 'user' ? 'Вы' : 'AI'}:</strong> ${content}
            </div>
        `;
        chatBox.scrollTop = chatBox.scrollHeight;
    }

    showLoadingIndicator() {
        const chatBox = document.getElementById('ai-chat-messages');
        chatBox.innerHTML += `
            <div class="message ai-loading">
                <div class="spinner-border spinner-border-sm"></div>
                <span>AI думает...</span>
            </div>
        `;
        chatBox.scrollTop = chatBox.scrollHeight;
    }

    removeLoadingIndicator() {
        document.querySelector('.ai-loading')?.remove();
    }

    // Работа с динамическими блоками
    initDynamicBlocks() {
        // Инициализация всех контролов с зависимостями
        document.querySelectorAll('[data-controls]').forEach(control => {
            // Обработчик изменения значения
            control.addEventListener('change', () => this.updateDependentFields(control));
            
            // Инициализация начального состояния
            this.updateDependentFields(control);
        });

        // Инициализация сложных условий для блоков
        document.querySelectorAll('[data-dependency]').forEach(block => {
            try {
                const dependency = JSON.parse(block.dataset.dependency);
                const control = document.querySelector(`[name="${dependency.field}"]`);
                
                if (control) {
                    control.addEventListener('change', () => {
                        this.updateBlockVisibility(block, dependency);
                    });
                    
                    this.updateBlockVisibility(block, dependency);
                }
            } catch (e) {
                console.error('Ошибка парсинга зависимостей:', e);
            }
        });
    }

    updateDependentFields(control) {
        try {
            if (!control.dataset.controls) return;
            
            const dependencies = JSON.parse(control.dataset.controls);
            Object.entries(dependencies).forEach(([targetId, conditions]) => {
                const target = document.querySelector(`[name="${targetId}"]`);
                if (!target) return;
                
                const shouldDisable = !conditions.values.includes(control.value);
                target.disabled = shouldDisable;
                
                if (shouldDisable) {
                    target.value = '';
                }
                
                // Обновление видимости связанных блоков
                const parentBlock = target.closest('.dynamic-block');
                if (parentBlock) {
                    parentBlock.style.display = shouldDisable ? 'none' : 'block';
                }
            });
        } catch (e) {
            console.error('Ошибка обновления зависимых полей:', e);
        }
    }

    updateBlockVisibility(block, dependency) {
        const control = document.querySelector(`[name="${dependency.field}"]`);
        if (!control) return;
        
        const conditionMet = this.checkDependencyCondition(control, dependency);
        
        if (conditionMet) {
            block.style.display = 'block';
            
            // Установка обязательности полей
            if (dependency.required) {
                block.querySelectorAll('input, select, textarea').forEach(field => {
                    field.required = true;
                });
            }
        } else {
            block.style.display = 'none';
            
            // Снятие обязательности и очистка значений
            block.querySelectorAll('input, select, textarea').forEach(field => {
                field.required = false;
                field.value = '';
            });
        }
    }

    checkDependencyCondition(control, dependency) {
        const value = control.value;
        
        switch (dependency.condition) {
            case 'equals': return value == dependency.value;
            case 'not_equals': return value != dependency.value;
            case 'contains': return value.includes(dependency.value);
            case 'greater_than': return parseFloat(value) > parseFloat(dependency.value);
            case 'less_than': return parseFloat(value) < parseFloat(dependency.value);
            case 'in': return dependency.values.includes(value);
            case 'not_in': return !dependency.values.includes(value);
            default: return false;
        }
    }

    // Контекстные подсказки
    async fetchContextualAdvice(fieldName) {
        try {
            const response = await fetch(`/api/ai/field-help/?field=${fieldName}`, {
                headers: {
                    'X-CSRFToken': this.getCSRFToken()
                }
            });
            
            const data = await response.json();
            
            if (data.status === 'success') {
                const adviceContainer = document.getElementById('contextual-advice');
                if (adviceContainer) {
                    adviceContainer.innerHTML = `
                        <div class="alert alert-info">
                            <h6>${data.field_label} - советы AI:</h6>
                            <p>${data.advice}</p>
                            ${data.examples ? `<small>Примеры: ${data.examples.join(', ')}</small>` : ''}
                        </div>
                    `;
                }
            }
        } catch (error) {
            console.error('Ошибка получения подсказки:', error);
        }
    }

    // Вспомогательные методы
    getCSRFToken() {
        return document.querySelector('[name=csrfmiddlewaretoken]')?.value || '';
    }

    getCurrentDocumentContext() {
        const form = document.getElementById('document-form');
        if (!form) return {};
        
        const formData = new FormData(form);
        const context = {};
        
        formData.forEach((value, key) => {
            context[key] = value;
        });
        
        return context;
    }

    // UI методы
    toggleAIPanel() {
        const panel = document.getElementById('ai-assistant-panel');
        panel?.classList.toggle('d-none');
    }
}

// Инициализация при загрузке страницы
document.addEventListener('DOMContentLoaded', () => {
    window.aiAssistant = new AIDocumentAssistant();
});

// Экспорт для тестирования
if (typeof module !== 'undefined' && module.exports) {
    module.exports = AIDocumentAssistant;
}

console.log('Dynamic blocks init:', document.querySelectorAll('.dynamic-block'));