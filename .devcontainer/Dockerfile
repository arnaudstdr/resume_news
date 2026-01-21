# syntax=docker/dockerfile:1

FROM python:3.12-slim

# --- Variables ---
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# --- System dependencies ---
RUN apt-get update && apt-get install -y \
    bash \
    curl \
    git \
    build-essential \
    ca-certificates \
    gnupg \
    sudo \
    libcairo2 \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libgdk-pixbuf-2.0-0 \
    libglib2.0-0 \
    libffi-dev \
    && rm -rf /var/lib/apt/lists/*

# --- Install Docker CLI ---
RUN curl -fsSL https://download.docker.com/linux/debian/gpg | gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg \
    && echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/debian $(. /etc/os-release && echo "$VERSION_CODENAME") stable" \
    | tee /etc/apt/sources.list.d/docker.list > /dev/null \
    && apt-get update \
    && apt-get install -y docker-ce-cli docker-compose-plugin \
    && rm -rf /var/lib/apt/lists/*

# --- Install Node.js (LTS) ---
RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs


RUN npm install -g npm@latest

# --- IA CLIs ---
RUN npm install -g @openai/codex
# RUN npm install -g @anthropic-ai/claude-code
# --- Upgrade pip ---
RUN python -m pip install --upgrade pip

# --- ML backend (PyTorch CPU) ---
RUN python -m pip install torch --index-url https://download.pytorch.org/whl/cpu

# --- Create non-root user ---
ARG USERNAME=vscode
ARG USER_UID=1000
ARG USER_GID=1000

RUN groupadd --gid $USER_GID $USERNAME \
    && useradd --uid $USER_UID --gid $USER_GID -m $USERNAME \
    && chown -R $USERNAME /home/$USERNAME \
    && usermod -aG docker $USERNAME 2>/dev/null || true \
    && echo "$USERNAME ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers.d/$USERNAME \
    && chmod 0440 /etc/sudoers.d/$USERNAME

USER $USERNAME
WORKDIR /workspace
