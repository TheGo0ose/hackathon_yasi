<div align="center">

# 🏆 RizzChecker AI

### ML-powered Credit Scoring Platform with AI Financial Advisor

[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Flutter](https://img.shields.io/badge/Flutter-Web-02569B?style=for-the-badge&logo=flutter&logoColor=white)](https://flutter.dev)
[![Telegram](https://img.shields.io/badge/Telegram-Mini_App-26A5E4?style=for-the-badge&logo=telegram&logoColor=white)](https://core.telegram.org/bots/webapps)
[![Python](https://img.shields.io/badge/Python-3.12+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![Render](https://img.shields.io/badge/Deploy-Render-46E3B7?style=for-the-badge&logo=render&logoColor=white)](https://render.com)

**RizzChecker** — платформа кредитного скоринга на базе ML с XAI-объяснениями и AI-советником.  
Один сервис: REST API + веб-приложение + Telegram Mini App + AI-чат.

[🌐 Live Demo](https://rizzchecker.onrender.com) · [🤖 Telegram Bot](https://t.me/megascoreanalyzerbot) · [📖 API Docs](https://rizzchecker.onrender.com/docs)

</div>

---

## 📋 Оглавление

- [Возможности](#-возможности)
- [Архитектура](#-архитектура)
- [Технологический стек](#-технологический-стек)
- [ML-модель](#-ml-модель)
- [API Reference](#-api-reference)
- [Быстрый старт](#-быстрый-старт)
- [Деплой](#-деплой)
- [Структура проекта](#-структура-проекта)
- [Команда](#-команда)

---

## ✨ Возможности

### 🎯 Кредитный скоринг
- **8 входных параметров** → мгновенное решение APPROVED / DECLINED
- **Кредитный балл** по шкале FICO (300–850)
- **Риск-сегментация**: low / medium / high / critical
- **XAI (Explainable AI)**: SHAP-значения для каждого фактора

### 🤖 AI Финансовый Советник
- Контекстный диалог на базе **Gemini 2.5 Flash** (OpenRouter)
- Получает ML-контекст: решение, вероятность, SHAP-вклады
- Даёт **конкретные пути к одобрению**: «если доход вырастет на 5000₽ — кредит будет одобрен»
- Поддержка истории диалога

### 📊 Кредитный Калькулятор
- **Аннуитетный** и **дифференцированный** расчёт
- Общая переплата за весь срок
- **DTI** (Debt-to-Income) с цветовой индикацией нагрузки
- Визуальная разбивка: тело кредита vs проценты

### 📥 CSV-импорт (Batch Scoring)
- Загрузка CSV-файла с заявками
- Пакетный скоринг через один API-вызов
- Дашборд: total / approved / declined / approval rate
- Таблица результатов с цветовой кодировкой

### 📱 Telegram Mini App
- Полнофункциональный веб-интерфейс внутри Telegram
- Адаптивный дизайн (мобильный + десктоп)
- Бот с FSM для скоринга через диалог

---

## 🏗 Архитектура

```
┌─────────────────────────────────────────────────────┐
│                    Render.com                        │
│                                                     │
│  ┌─────────────┐    ┌────────────────────────────┐  │
│  │  Telegram    │    │     FastAPI Backend         │  │
│  │  Bot (aiogram)│───▶│                            │  │
│  │  (background)│    │  /api/v1/scoring/predict    │  │
│  └──────┬───────┘    │  /api/v1/scoring/batch      │  │
│         │            │  /api/v1/advisor/chat        │  │
│         │            │  /api/v1/health              │  │
│         ▼            │                            │  │
│  ┌─────────────┐    │  ┌────────────────────┐     │  │
│  │  Telegram    │    │  │  ML Engine (NumPy) │     │  │
│  │  Mini App    │◀───│  │  Logistic Reg +    │     │  │
│  │  (Flutter    │    │  │  SHAP Explainer    │     │  │
│  │   Web)       │    │  └────────────────────┘     │  │
│  └──────────────┘    │                            │  │
│                      │  ┌────────────────────┐     │  │
│                      │  │  AI Advisor         │     │  │
│                      │  │  (OpenRouter →      │     │  │
│                      │  │   Gemini 2.5 Flash) │     │  │
│                      │  └────────────────────┘     │  │
│                      └────────────────────────────┘  │
└─────────────────────────────────────────────────────┘
```

---

## 🛠 Технологический стек

| Компонент | Технология |
|-----------|-----------|
| **Backend** | FastAPI, Uvicorn, Pydantic v2 |
| **ML Engine** | NumPy (чистая реализация LogReg, без sklearn) |
| **XAI** | SHAP-эквивалентные logit contributions |
| **AI Advisor** | OpenAI SDK → OpenRouter → Gemini 2.5 Flash |
| **Frontend** | Flutter Web (Dart) |
| **Telegram Bot** | aiogram 3, FSM (MemoryStorage) |
| **Deploy** | Docker multi-stage, Render.com |

---

## 🧠 ML-модель

### Обучение
Модель обучена в `ai_model/train_model.py` на синтетическом датасете кредитных заявок.

### Алгоритм
**L2-регуляризованная логистическая регрессия** (реализация на NumPy):
- Стандартизация признаков (z-score)
- Логит: `intercept + Σ(z_i × coef_i)`
- Sigmoid → P(default) ∈ [0, 1]

### Признаки (8 штук)

| Признак | Тип | Описание |
|---------|-----|----------|
| `age` | int | Возраст заёмщика |
| `monthly_income` | float | Ежемесячный доход (₽) |
| `employment_years` | float | Стаж работы (лет) |
| `loan_amount` | float | Сумма кредита (₽) |
| `loan_term_months` | int | Срок кредита (мес.) |
| `interest_rate` | float | Процентная ставка (%) |
| `past_due_30d` | int | Просрочки 30+ дней |
| `inquiries_6m` | int | Запросы за 6 мес. |

### Решение
- **Порог**: P(default) > 0.25 → `DECLINED`
- **Кредитный балл**: 300–850 (FICO-маппинг)
- **Риск-сегменты**: low (≤15%), medium (≤35%), high (≤60%), critical (>60%)

---

## 📡 API Reference

### `POST /api/v1/scoring/predict`

Скоринг одной заявки.

**Request:**
```json
{
  "age": 29,
  "monthly_income": 85000,
  "employment_years": 3.5,
  "loan_amount": 500000,
  "loan_term_months": 36,
  "interest_rate": 14.5,
  "past_due_30d": 0,
  "inquiries_6m": 1
}
```

**Response:**
```json
{
  "decision": "APPROVED",
  "probability_of_default": 0.12,
  "credit_score": 741,
  "risk_segment": {
    "label": "low",
    "color": "#22C55E",
    "description": "Низкий риск дефолта"
  },
  "shap_values": {
    "base_value": 0.262,
    "feature_contributions": {
      "age": -0.045,
      "monthly_income": -0.182,
      "employment_years": -0.067,
      "loan_amount": 0.031,
      "loan_term_months": -0.012,
      "interest_rate": 0.055,
      "past_due_30d": -0.198,
      "inquiries_6m": -0.023
    }
  },
  "model_version": "l2_logistic_regression_numpy/baseline_8_features",
  "threshold_used": 0.25
}
```

### `POST /api/v1/scoring/batch`

Пакетный скоринг (массив заявок → массив результатов).

### `POST /api/v1/advisor/chat`

AI-советник с ML-контекстом.

**Request:**
```json
{
  "user_message": "Почему мне отказали?",
  "ml_context": {
    "decision": "DECLINED",
    "probability": 0.42,
    "risk_segment": "high",
    "shap_values": { ... }
  },
  "chat_history": []
}
```

📖 **Полная документация**: [/docs](https://rizzchecker.onrender.com/docs) (Swagger UI)

---

## 🚀 Быстрый старт

### Требования
- Python 3.12+
- Flutter SDK 3.2+
- Git

### 1. Клонировать репо
```bash
git clone https://github.com/TheGo0ose/hackathon_yasi.git
cd hackathon_yasi
```

### 2. Запустить бэкенд
```bash
cd backend
pip install -r requirements.txt

# Создать .env
cat > .env << EOF
USE_MOCK_SCORER=false
MODEL_PATH=app/ml_inference/models/scoring_model.json
DEFAULT_THRESHOLD=0.25
CORS_ORIGINS=*
OPENROUTER_API_KEY=your_key_here
EOF

uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### 3. Запустить фронтенд (dev mode)
```bash
cd flutter_frontend
flutter pub get
flutter run -d chrome
```

### 4. Запустить Telegram бота
```bash
cd tg_bot
pip install -r requirements.txt

# Создать .env
cat > .env << EOF
BOT_TOKEN=your_bot_token
BACKEND_URL=http://localhost:8000
WEB_APP_URL=http://localhost:8000
EOF

python bot.py
```

---

## ☁️ Деплой

### Render.com (Docker, бесплатно)

1. Fork / подключи репо на [render.com](https://render.com)
2. **New Web Service** → Docker → Free plan
3. Добавь Environment Variables:

| Key | Value |
|-----|-------|
| `USE_MOCK_SCORER` | `false` |
| `MODEL_PATH` | `app/ml_inference/models/scoring_model.json` |
| `DEFAULT_THRESHOLD` | `0.25` |
| `CORS_ORIGINS` | `*` |
| `OPENROUTER_API_KEY` | `sk-or-v1-...` |
| `BOT_TOKEN` | `from @BotFather` |
| `BACKEND_URL` | `https://your-app.onrender.com` |
| `WEB_APP_URL` | `https://your-app.onrender.com` |

4. Deploy — получи HTTPS URL для Mini App

---

## 📁 Структура проекта

```
hackathon_yasi/
├── backend/                    # FastAPI backend
│   ├── app/
│   │   ├── api/v1/            # REST endpoints
│   │   │   ├── scoring.py     # /predict + /batch
│   │   │   ├── advisor.py     # /advisor/chat (LLM)
│   │   │   └── router.py
│   │   ├── ml_inference/      # ML scoring engine
│   │   │   ├── real_scorer.py # NumPy LogReg inference
│   │   │   ├── mock_scorer.py # Dev/test mock
│   │   │   └── models/        # scoring_model.json
│   │   ├── services/
│   │   │   ├── scoring_service.py  # Score → FICO → Risk
│   │   │   └── advisor_service.py  # OpenRouter LLM
│   │   ├── schemas/           # Pydantic models
│   │   ├── config.py          # Settings (env vars)
│   │   └── main.py            # FastAPI app + SPA serving
│   ├── requirements.txt
│   └── .env
│
├── flutter_frontend/           # Flutter Web UI
│   ├── lib/
│   │   ├── screens/
│   │   │   ├── landing_page.dart    # Hero + nav
│   │   │   ├── form_page.dart       # 8-field scoring form
│   │   │   ├── result_page.dart     # Score + speedometer
│   │   │   ├── ai_chat_page.dart    # AI advisor chat
│   │   │   ├── calculator_page.dart # Credit calculator
│   │   │   └── import_page.dart     # CSV batch import
│   │   ├── widgets/
│   │   │   ├── smoke_layer.dart     # Animated background
│   │   │   └── cut_corners.dart     # Custom button style
│   │   ├── theme/app_theme.dart     # Design tokens
│   │   ├── config.dart              # API URL config
│   │   └── main.dart
│   ├── web/index.html          # Telegram Web App SDK
│   └── pubspec.yaml
│
├── tg_bot/                     # Telegram Bot (aiogram 3)
│   ├── bot.py                  # Entry point
│   ├── handlers.py             # FSM + message handlers
│   ├── keyboards.py            # Inline/reply keyboards
│   ├── states.py               # FSM states
│   └── config.py               # Env loader
│
├── ai_model/                   # ML training pipeline
│   ├── train_model.py          # LogReg training script
│   ├── baseline.ipynb          # EDA notebook
│   └── data/                   # Training data
│
├── Dockerfile                  # Multi-stage (Flutter + Python)
├── start.sh                    # Runs bot + backend together
├── render.yaml                 # Render.com config
└── README.md
```

---

## 👥 Команда

Проект создан на хакатоне командой **YASI**.

---

<div align="center">

**Built with ❤️ and ML**

</div>