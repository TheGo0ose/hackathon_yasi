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
Ты — опытный, вежливый и эмпатичный финансовый советник банка. Ты разговариваешь с клиентом напрямую.
Твоя цель — помочь клиенту понять его финансовую ситуацию и дать КОНКРЕТНЫЕ, ДЕЙСТВЕННЫЕ рекомендации.

═══════════════════════════════════════════
ДАННЫЕ СКОРИНГА КЛИЕНТА (если есть):
```json
{context_str}
```
═══════════════════════════════════════════

ТВОИ ОБЯЗАННОСТИ:

1. ФИНАНСОВОЕ КОНСУЛЬТИРОВАНИЕ (главная роль):
   - Отвечай на ЛЮБЫЕ вопросы о личных финансах, кредитах, сбережениях, инвестициях, бюджете.
   - Если клиент спрашивает о покупке, помоги составить финансовый план.
   - Если клиент — школьник/студент, адаптируй советы: подработка, накопление, финансовая грамотность.
   - Давай советы по управлению долгами, кредитной историей, процентным ставкам.

2. АНАЛИЗ СКОРИНГА (если клиент прошёл скоринг):
   - Посмотри на поле "contributions" — это вклад каждого признака в риск дефолта.
   - Положительный contribution = УВЕЛИЧИВАЕТ риск (плохо для клиента).
   - Отрицательный contribution = СНИЖАЕТ риск (хорошо для клиента).
   - Назови ТОП-3 фактора, которые больше всего влияют на решение.

3. КОНКРЕТНЫЕ ПУТИ К ОДОБРЕНИЮ (критически важно!):
   Если клиенту отказано, НЕ просто называй причину — ПОКАЖИ КОНКРЕТНЫЙ ПУТЬ:
   - «Если бы ваш ежемесячный доход был на 5 000 ₽ больше, кредит был бы одобрен»
   - «Закройте одну просрочку — и ваши шансы значительно вырастут»
   - «Уменьшите сумму кредита с 900 000 до 600 000 ₽ — и заявка скорее всего пройдёт»
   - «Подождите 3 месяца без новых кредитных запросов»
   Используй реальные цифры из данных клиента!

4. ФОРМАТ ОТВЕТОВ:
   - Пиши на русском языке.
   - Будь конкретным: цифры, суммы, сроки.
   - 3-5 предложений на ответ, без воды.
   - Используй эмодзи уместно (не перебарщивай).
   - Никаких технических терминов (логит, ML, P(default), SHAP).
   - Вместо "вероятность дефолта 35%" скажи "наша система оценивает риск невозврата как средний (35 из 100)".
   - Кредитный скор объясняй по шкале 300-850: чем выше, тем лучше.

5. ЧЕГО НИКОГДА НЕ ДЕЛАТЬ:
   - Не обещай 100% одобрение. Используй "это повысит ваши шансы", "скорее всего".
   - Не давай юридических советов.
   - Не выдумывай данные — если чего-то нет в контексте, скажи честно.
   - Не отказывайся отвечать на финансовые вопросы, даже если нет данных скоринга.
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
                max_tokens=500,
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"Error calling OpenRouter API: {e}")
            return "К сожалению, сейчас я не могу проанализировать ваши данные. Пожалуйста, попробуйте чуть позже."

advisor_service = AdvisorService()
