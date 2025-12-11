# Combined Dockerfile for monorepo deployment on Fly.io
# Builds frontend and serves via FastAPI backend

# Stage 1: Build frontend
FROM node:20-slim AS frontend-builder

WORKDIR /frontend
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

# Stage 2: Python backend with static frontend
FROM python:3.13-slim-bookworm

WORKDIR /app

# Install backend dependencies
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend code
COPY backend/ .

# Copy frontend build output
COPY --from=frontend-builder /frontend/dist ./static

# Expose port 8080 (Fly.io standard)
EXPOSE 8080

# Run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
