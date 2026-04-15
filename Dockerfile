FROM python:3.12-slim

# Install uv from the official image
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Set the working directory
WORKDIR /app

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Copy the dependencies locking file and pyproject.toml first to leverage Docker cache
COPY pyproject.toml uv.lock ./

# Install dependencies (without installing the project itself yet)
RUN uv sync --frozen --no-install-workspace --no-cache

# Copy the rest of the application
COPY . .

# Install the project
RUN uv sync --frozen --no-cache

# Start the ADK web interface by default
CMD ["uv", "run", "adk", "web"]
