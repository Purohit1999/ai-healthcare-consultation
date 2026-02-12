# Stage 1: Build Next.js static export
FROM node:22-alpine AS frontend-builder

WORKDIR /app

# Install deps (better cache)
COPY package.json package-lock.json ./
RUN npm ci

# Copy only what we need
COPY next.config.ts tsconfig.json postcss.config.mjs eslint.config.mjs ./
COPY public ./public
COPY src ./src

# Build-time public env var (safe to bake in)
ARG NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY
ENV NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=${NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY}

# Build -> generates /app/out
RUN npm run build


# Stage 2: Python runtime
FROM python:3.12-slim

WORKDIR /app

# (Optional but nice) Faster + cleaner
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install Python deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend server
COPY api/server.py ./server.py

# Copy built static site
COPY --from=frontend-builder /app/out ./static

# Healthcheck (App Runner may ignore this, but it's fine)
HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health')"

EXPOSE 8000

CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8000"]
