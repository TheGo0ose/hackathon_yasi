# ============================================================
# Stage 1: Build Flutter web
# ============================================================
FROM ghcr.io/cirruslabs/flutter:latest AS flutter-build

WORKDIR /app/flutter_frontend
COPY flutter_frontend/pubspec.yaml flutter_frontend/pubspec.lock ./
RUN flutter pub get

COPY flutter_frontend/ ./
RUN flutter build web --dart-define=PRODUCTION=true --release

# ============================================================
# Stage 2: Python backend + serve Flutter
# ============================================================
FROM python:3.12-slim

WORKDIR /app

# Install backend dependencies
COPY backend/requirements.txt ./backend-requirements.txt
RUN pip install --no-cache-dir -r backend-requirements.txt

# Install bot dependencies
COPY tg_bot/requirements.txt ./bot-requirements.txt
RUN pip install --no-cache-dir -r bot-requirements.txt

# Copy backend code
COPY backend/ ./backend/

# Copy bot code
COPY tg_bot/ ./tg_bot/

# Copy Flutter build from stage 1
COPY --from=flutter-build /app/flutter_frontend/build/web ./flutter_frontend/build/web

# Copy startup script
COPY start.sh ./start.sh
RUN chmod +x ./start.sh

# Expose port
EXPOSE 8000

# Start both bot + backend
CMD ["./start.sh"]
