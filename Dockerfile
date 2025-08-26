# Dockerfile for PCD Visualizer - Development and Testing Environment
# Multi-stage build for efficient containerization

# Build stage
FROM python:3.10-slim as builder

# Install system dependencies for building
RUN apt-get update && apt-get install -y \
    build-essential \
    cmake \
    git \
    libgl1-mesa-dev \
    libglu1-mesa-dev \
    libxrandr2 \
    libxrandr2 \
    libxss1 \
    libxcursor1 \
    libxcomposite1 \
    libasound2 \
    libxi6 \
    libxtst6 \
    libqt6gui6 \
    libqt6widgets6 \
    libqt6opengl6-dev \
    qt6-base-dev \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy requirements and install Python dependencies
COPY requirements*.txt ./
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir -r requirements-build.txt

# Runtime stage
FROM python:3.10-slim

# Install runtime system dependencies
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libxrandr2 \
    libxss1 \
    libxcursor1 \
    libxcomposite1 \
    libasound2 \
    libxi6 \
    libxtst6 \
    libqt6gui6 \
    libqt6widgets6 \
    libqt6opengl6 \
    qt6-qpa-plugins \
    x11-apps \
    xvfb \
    && rm -rf /var/lib/apt/lists/*

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Set up environment variables for GUI applications
ENV QT_X11_NO_MITSHM=1
ENV QT_QPA_PLATFORM=xcb
ENV DISPLAY=:0
ENV PYTHONPATH=/app

# Create app user for security
RUN groupadd -r pcduser && useradd -r -g pcduser pcduser

# Create application directory
WORKDIR /app

# Copy application files
COPY --chown=pcduser:pcduser . .

# Switch to non-root user
USER pcduser

# Create entry point script
RUN echo '#!/bin/bash\n\
set -e\n\
\n\
# Check if we have a display\n\
if [ -z "$DISPLAY" ]; then\n\
    echo "Starting virtual display..."\n\
    export DISPLAY=:99\n\
    Xvfb :99 -screen 0 1024x768x24 > /dev/null 2>&1 &\n\
    sleep 2\n\
fi\n\
\n\
# Run the application\n\
exec python -m pcd_visualizer.main "$@"\n' > /usr/local/bin/pcd-visualizer && \
    chmod +x /usr/local/bin/pcd-visualizer

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import pcd_visualizer; print('OK')" || exit 1

# Default command
CMD ["python", "-m", "pcd_visualizer.main"]

# Labels
LABEL maintainer="PCD Visualizer Team <contact@pcdvisualizer.com>"
LABEL version="2.0.0"
LABEL description="Point Cloud Data Visualizer"
LABEL org.opencontainers.image.source="https://github.com/pcdvisualizer/pcd-visualizer"
LABEL org.opencontainers.image.documentation="https://pcdvisualizer.readthedocs.io/"
LABEL org.opencontainers.image.licenses="MIT"