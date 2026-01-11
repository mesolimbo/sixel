# Dockerfile for running sixel snake game E2E tests
#
# This container provides a headless environment for testing sixel rendering
# without requiring an actual sixel-capable terminal.

FROM python:3.13-slim

# Set working directory
WORKDIR /app

# Install pipenv and system dependencies
RUN pip install --no-cache-dir pipenv pytest

# Copy Pipfile first for dependency caching
COPY Pipfile Pipfile.lock* ./

# Install dependencies
RUN pipenv install --system --deploy --ignore-pipfile || pipenv install --system

# Copy the application code
COPY . .

# Set PYTHONPATH for imports
ENV PYTHONPATH=/app

# Default command runs the E2E render tests
CMD ["pytest", "tests/test_render_e2e.py", "-v", "--tb=short"]
