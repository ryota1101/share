# Frontend Dockerfile for Next.js
FROM node:18-alpine

WORKDIR /app

# Install dependencies
COPY package*.json ./
RUN npm ci

# Copy source code
COPY . .

# Create .next directory with proper permissions
RUN mkdir -p .next && chown -R node:node .next

# Switch to non-root user
USER node

# Expose port
EXPOSE 3000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:3000 || exit 1

# Development command (will be overridden by docker-compose)
CMD ["npm", "run", "dev"]