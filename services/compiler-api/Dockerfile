# syntax=docker/dockerfile:1
FROM python:3.13-slim

# --- system deps -----------------------------------------------------------
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# --- non-root user ---------------------------------------------------------
RUN useradd --create-home --uid 1001 appuser

# --- workdir ---------------------------------------------------------------
WORKDIR /app

# --- install hcc-compiler as editable package first -----------------------
# Copy only the minimum files needed for editable install so layer is cacheable.
COPY pyproject.toml ./
COPY src/ ./src/

RUN pip install --no-cache-dir -e .

# --- install FastAPI sidecar deps -----------------------------------------
COPY services/compiler-api/requirements.txt ./services/compiler-api/requirements.txt
RUN pip install --no-cache-dir -r services/compiler-api/requirements.txt

# --- copy library content (atoms + patterns + library.db if present) ------
COPY library/ ./library/

# Copy library.db from project root if it exists (build-time bake-in).
# At runtime the Fly volume at /data/library.db takes precedence via env.
COPY --chown=appuser:appuser library.db* /data-seed/

# --- copy sidecar source ---------------------------------------------------
COPY services/compiler-api/ ./services/compiler-api/

# --- data directory (Fly volume mount point) --------------------------------
RUN mkdir -p /data && chown appuser:appuser /data

# --- drop privileges -------------------------------------------------------
USER appuser

# --- expose ----------------------------------------------------------------
EXPOSE 8080

# --- entrypoint ------------------------------------------------------------
# The sidecar imports from services/compiler-api/ so we run from there.
# LIBRARY_DB_PATH defaults to /data/library.db; the Fly volume is mounted at /data.
WORKDIR /app/services/compiler-api
ENV PYTHONUNBUFFERED=1
ENV PORT=8080

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
