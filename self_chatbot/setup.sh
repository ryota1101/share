#!/bin/bash

# Multi-LLM Chat Setup Script
# This script sets up the development environment

set -e

echo "🚀 Setting up Multi-LLM Chat application..."

# Create project structure
echo "📁 Creating project structure..."
mkdir -p backend/{config,models,utils,routes}
mkdir -p frontend/{components,pages,styles,utils}
mkdir -p config
mkdir -p logs

# Copy environment file
if [ ! -f .env ]; then
    echo "📋 Creating .env file from template..."
    cp .env.example .env
    echo "⚠️  Please edit .env file with your API keys before running the application"
fi

# Create .gitignore
echo "📝 Creating .gitignore..."
cat > .gitignore << 'EOF'
# Environment files
.env
.env.local
.env.production

# Database
postgres_data/

# Python
__pycache__/
*.pyc
*.pyo
*.pyd
.Python
env/
venv/
.venv/
pip-log.txt
pip-delete-this-directory.txt
*.egg-info/
dist/
build/

# Node.js
node_modules/
npm-debug.log*
yarn-debug.log*
yarn-error.log*
.next/
.vercel
*.tgz
*.tar.gz

# IDEs
.vscode/
.idea/
*.swp
*.swo
*~

# OS
.DS_Store
Thumbs.db

# Logs
logs/
*.log

# Docker
docker-compose.override.yml
EOF

# Create initial package.json for frontend
echo "📦 Creating frontend package.json..."
cat > frontend/package.json << 'EOF'
{
  "name": "multi-llm-chat-frontend",
  "version": "1.0.0",
  "private": true,
  "scripts": {
    "dev": "next dev",
    "build": "next build",
    "start": "next start",
    "lint": "next lint"
  },
  "dependencies": {
    "next": "14.0.3",
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "axios": "^1.6.2",
    "socket.io-client": "^4.7.4",
    "react-markdown": "^9.0.1",
    "lucide-react": "^0.294.0",
    "@headlessui/react": "^1.7.17",
    "classnames": "^2.3.2"
  },
  "devDependencies": {
    "@types/node": "^20.9.0",
    "@types/react": "^18.2.37",
    "@types/react-dom": "^18.2.15",
    "autoprefixer": "^10.4.16",
    "eslint": "^8.54.0",
    "eslint-config-next": "14.0.3",
    "postcss": "^8.4.31",
    "tailwindcss": "^3.3.5",
    "typescript": "^5.2.2"
  }
}
EOF

# Create basic Next.js config
echo "⚙️ Creating Next.js configuration..."
cat > frontend/next.config.js << 'EOF'
/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  images: {
    domains: ['localhost'],
  },
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: `${process.env.NEXT_PUBLIC_API_URL}/:path*`,
      },
    ];
  },
};

module.exports = nextConfig;
EOF

# Create Tailwind config
cat > frontend/tailwind.config.js << 'EOF'
/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './pages/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
    './app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        'chat-bg': '#f7f7f8',
        'chat-user': '#007bff',
        'chat-assistant': '#6c757d',
      },
    },
  },
  plugins: [],
}
EOF

# Create PostCSS config
cat > frontend/postcss.config.js << 'EOF'
module.exports = {
  plugins: {
    tailwindcss: {},
    autoprefixer: {},
  },
}
EOF

echo "✅ Project structure created successfully!"
echo ""
echo "📋 Next steps:"
echo "1. Edit .env file with your API keys"
echo "2. Run 'docker-compose up --build' to start the application"
echo "3. Access the application at http://localhost:3000"
echo ""
echo "🔧 For development:"
echo "- Frontend: http://localhost:3000"
echo "- Backend API: http://localhost:5000"
echo "- Database: localhost:5432"
echo ""
echo "📚 Configuration:"
echo "- Edit config/models.yaml to add new AI models"
echo "- Database will be initialized automatically on first run"