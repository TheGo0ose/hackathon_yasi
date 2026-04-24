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

# Install Python dependencies
COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend code
COPY backend/ ./backend/

# Copy Flutter build from stage 1
COPY --from=flutter-build /app/flutter_frontend/build/web ./flutter_frontend/build/web

# Set working directory to backend
WORKDIR /app/backend

# Expose port (Render uses PORT env var)
EXPOSE 8000

# Start the server — Render sets PORT automatically
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
