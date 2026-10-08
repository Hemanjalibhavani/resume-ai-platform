FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
COPY requirements.txt requirements-ai.txt ./
# Set INSTALL_AI=true to add sentence-transformers + FAISS (much larger image)
ARG INSTALL_AI=false
RUN pip install --no-cache-dir -r requirements.txt && \
    if [ "$INSTALL_AI" = "true" ]; then pip install --no-cache-dir -r requirements-ai.txt; fi
COPY backend ./backend
COPY frontend ./frontend
RUN mkdir -p uploads vector_store
EXPOSE 8000
CMD ["sh", "-c", "uvicorn backend.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
