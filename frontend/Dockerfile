FROM node:20-bookworm

# Enable corepack for pnpm
RUN corepack enable
RUN corepack prepare pnpm@latest --activate
ENV PNPM_HOME=/usr/local/bin
ENV PATH="$PNPM_HOME:$PATH"

WORKDIR /app

# Copy only package files first
COPY package*.json ./
COPY pnpm-lock.yaml ./

# Install Quasar CLI
RUN pnpm add -g @quasar/cli

# 3. Install rollup specifically for the platform
RUN pnpm install


# Copy source files AFTER dependencies are installed
COPY src/ ./src/
COPY public/ ./public/
COPY *.config.* ./
COPY quasar.config.js ./
COPY index.html ./

# Build the app
RUN pnpm run build

EXPOSE 9000
CMD ["pnpm", "exec", "quasar", "dev"]