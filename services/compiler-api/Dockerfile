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
RUN chmod +x ./services/compiler-api/entrypoint.sh

# --- data directory (Fly volume mount point) --------------------------------
# Seed dir + volume dir both owned by appuser so the entrypoint cp succeeds.
RUN mkdir -p /data /data-seed && chown -R appuser:appuser /data /data-seed

# --- drop privileges -------------------------------------------------------
USER appuser

# --- expose ----------------------------------------------------------------
EXPOSE 8080

# --- entrypoint ------------------------------------------------------------
# entrypoint.sh seeds /data/library.db from /data-seed/library.db if the
# baked seed is newer than (or replaces a missing) volume copy, then exec's
# uvicorn. Keeps deploys self-updating without needing fly ssh.
WORKDIR /app/services/compiler-api
ENV PYTHONUNBUFFERED=1
ENV PORT=8080

CMD ["./entrypoint.sh"]
