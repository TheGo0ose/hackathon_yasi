import logging
from typing import Dict, Any, List
from openai import AsyncOpenAI
import json

from app.config import settings
from app.schemas.advisor import AdvisorRequest, Message

logger = logging.getLogger(__name__)

class AdvisorService:
    def __init__(self):
        # OpenRouter uses the exact same interface as OpenAI
        self.client = AsyncOpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=settings.openrouter_api_key,
        )
        self.model_name = "google/gemini-2.5-flash"  # You can adjust this to any other available model

    def _generate_system_prompt(self, ml_context: Dict[str, Any]) -> str:
        """
        Generates the strict instructions for the LLM based on the user's ML scoring context.
        """
        context_str = json.dumps(ml_context, ensure_ascii=False, indent=2)
        
        prompt = f"""
Ты вежливый, профессиональный и эмпатичный финансовый консультант банка.
Твоя задача — помочь клиенту понять его кредитный скоринг и дать советы по его улучшению.

Ниже приведены СУХИЕ ФАКТЫ из нашей ML-модели по текущей заявке клиента:
```json
{context_str}
```

ПРАВИЛА ТВОЕЙ РАБОТЫ:
1. Если вероятность дефолта (P(default)) высокая, мягко объясни, что банк видит риски.
2. Опирайся на "contributions" (вклады признаков). Положительный вклад увеличивает риск дефолта (плохо). Отрицательный — снижает (хорошо). Укажи клиенту на его слабые места.
3. Давай ТОЛЬКО конкретные, выполнимые советы (например: "постарайтесь вносить платежи вовремя", "уменьшите сумму займа", "закройте старые кредитные карты").
4. Отвечай кратко, без воды, 3-4 предложения на один ответ.
5. Никогда не обещай 100% выдачу кредита, используй формулировки "это повысит ваши шансы".
6. Не используй технические термины вроде "логит", "ML", "P(default)". Переводи их на человеческий язык.
"""
        return prompt.strip()

    async def get_advice(self, request: AdvisorRequest) -> str:
        """
        Calls the LLM (via OpenRouter) with the system prompt, chat history, and user's new message.
        """
        # Build the messages array
        messages = [
            {"role": "system", "content": self._generate_system_prompt(request.ml_context)}
        ]
        
        # Append history
        for msg in request.chat_history:
            messages.append({"role": msg.role, "content": msg.content})
            
        # Append current user query
        messages.append({"role": "user", "content": request.user_message})

        try:
            response = await self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"Error calling OpenRouter API: {e}")
            return "К сожалению, сейчас я не могу проанализировать ваши данные. Пожалуйста, попробуйте чуть позже."

advisor_service = AdvisorService()
