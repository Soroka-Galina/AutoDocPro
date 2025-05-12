# documents/services.py
import requests
import json
from django.conf import settings
from django.core.cache import cache
from .models import AIRequestHistory
import logging

logger = logging.getLogger('deepseek')

class DeepSeekIntegration:
    @classmethod
    def _make_request(cls, endpoint, payload):
        """
        Выполняет запрос к API DeepSeek с кэшированием и логированием.
        
        Args:
            endpoint (str): Конечная точка API (например, 'chat/completions')
            payload (dict): Данные для отправки в API
            
        Returns:
            dict: Ответ от API
            
        Raises:
            requests.exceptions.RequestException: Если произошла ошибка при запросе
        """
        headers = {
            "Authorization": f"Bearer {settings.DEEPSEEK_API_KEY}",
            "Content-Type": "application/json"
        }
        
        # Генерируем уникальный ключ кэша на основе endpoint и payload
        cache_key = f"deepseek_{endpoint}_{hash(json.dumps(payload, sort_keys=True))}"
        cached_response = cache.get(cache_key)
        
        if cached_response:
            logger.debug(f"Возвращаем закэшированный ответ для ключа: {cache_key}")
            return cached_response

        try:
            logger.info(f"Отправка запроса к DeepSeek API: {endpoint}")
            response = requests.post(
                f"{settings.DEEPSEEK_API_URL}/{endpoint}",
                headers=headers,
                json=payload,
                timeout=settings.DEEPSEEK_TIMEOUT
            )
            response.raise_for_status()
            
            result = response.json()
            
            # Сохраняем в кэш
            cache.set(cache_key, result, settings.AI_CONFIG['CACHE_TIMEOUT'])
            logger.debug(f"Ответ сохранен в кэш с ключом: {cache_key}")
            
            # Логируем успешный запрос в базу данных
            AIRequestHistory.objects.create(
                request_type=endpoint,
                request_data=payload,
                response_data=result,
                api_endpoint=endpoint,
                model_used=settings.DEEPSEEK_MODEL
            )
            
            return result
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Ошибка при запросе к DeepSeek API: {str(e)}")
            
            # Логируем ошибку в базу данных
            AIRequestHistory.objects.create(
                request_type=endpoint,
                request_data=payload,
                response_data={"error": str(e)},
                is_error=True,
                api_endpoint=endpoint,
                model_used=settings.DEEPSEEK_MODEL
            )
            raise

    @classmethod
    def generate_text(cls, prompt, max_tokens=None, temperature=None):
        """
        Генерирует текст с помощью DeepSeek API.
        
        Args:
            prompt (str): Текст запроса
            max_tokens (int, optional): Максимальное количество токенов в ответе
            temperature (float, optional): Параметр температуры для генерации
            
        Returns:
            dict: Ответ от API с сгенерированным текстом
        """
        payload = {
            "model": settings.DEEPSEEK_MODEL,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens or settings.AI_CONFIG['MAX_TOKENS'],
            "temperature": temperature or settings.AI_CONFIG['TEMPERATURE']
        }
        return cls._make_request("chat/completions", payload)