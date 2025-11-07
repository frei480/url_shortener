FROM python:3.13-slim 

# Copy uv binaries from the official uv image
COPY --from=ghcr.io/astral-sh/uv:0.8.21 /uv /uvx /bin/

WORKDIR /app
ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy

# Install dependencies
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --locked --no-install-project

# Copy project files needed for dependency installation
COPY uv.lock pyproject.toml ./

# Install dependencies using uv sync with a cache mount
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --no-install-project --no-dev

# copy app
COPY src/backend/ .

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked

CMD ["uv", "run","main.py"]