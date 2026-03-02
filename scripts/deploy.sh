#!/bin/bash

# Eliza Lobster - Deployment Script
# Deploys the application to various platforms

set -e

echo "╔════════════════════════════════════════╗"
echo "║    Eliza Lobster - Deployment Tool     ║"
echo "╚════════════════════════════════════════╝"
echo

# Check prerequisites
check_prerequisites() {
    echo "Checking prerequisites..."
    
    if ! command -v node &> /dev/null; then
        echo "❌ Node.js not found"
        exit 1
    fi
    echo "✅ Node.js found: $(node --version)"
    
    if ! command -v npm &> /dev/null; then
        echo "❌ npm not found"
        exit 1
    fi
    echo "✅ npm found: $(npm --version)"
    
    echo
}

# Build the project
build_project() {
    echo "Building project..."
    npm install
    npm run build
    echo "✅ Build successful"
    echo
}

# Deploy to Railway.app
deploy_railway() {
    echo "🚂 Deploying to Railway..."
    
    if ! command -v railway &> /dev/null; then
        echo "Installing Railway CLI..."
        npm install -g @railway/cli
    fi
    
    railway link
    railway up
    echo "✅ Deployment to Railway complete!"
    echo "View logs with: railway logs"
    echo
}

# Deploy to Docker
deploy_docker() {
    echo "🐋 Preparing Docker deployment..."
    
    if [ ! -f "Dockerfile" ]; then
        echo "Creating Dockerfile..."
        cat > Dockerfile << 'EOF'
FROM node:18-alpine

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm install

# Copy source
COPY . .

# Build TypeScript
RUN npm run build

# Expose port
EXPOSE 3000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD node -e "require('http').get('http://localhost:3000/health', (r) => {if (r.statusCode !== 200) throw new Error(r.statusCode)})"

# Start application
CMD ["npm", "start"]
EOF
        echo "✅ Dockerfile created"
    fi
    
    if command -v docker &> /dev/null; then
        docker build -t eliza-lobster:latest .
        echo "✅ Docker image built"
        echo
        echo "To run: docker run -p 3000:3000 --env-file .env eliza-lobster:latest"
    else
        echo "⚠️  Docker not installed. Dockerfile created but image not built."
    fi
    echo
}

# Deploy to Heroku
deploy_heroku() {
    echo "🚀 Deploying to Heroku..."
    
    if ! command -v heroku &> /dev/null; then
        echo "Installing Heroku CLI..."
        npm install -g heroku
    fi
    
    if [ ! -f "Procfile" ]; then
        echo "Creating Procfile..."
        echo "web: npm start" > Procfile
    fi
    
    heroku login
    heroku create $(basename $(pwd))
    git push heroku main
    heroku config:set $(cat .env | tr '\n' ' ')
    echo "✅ Deployment to Heroku complete!"
    echo
}

# Show menu
show_menu() {
    echo "Select deployment target:"
    echo "1) Railway (recommended)"
    echo "2) Docker"
    echo "3) Heroku"
    echo "4) Build only"
    echo "5) Exit"
    echo
    read -p "Enter choice (1-5): " choice
}

# Main
main() {
    check_prerequisites
    
    while true; do
        show_menu
        
        case $choice in
            1)
                build_project
                deploy_railway
                break
                ;;
            2)
                build_project
                deploy_docker
                break
                ;;
            3)
                build_project
                deploy_heroku
                break
                ;;
            4)
                build_project
                break
                ;;
            5)
                echo "Exiting..."
                exit 0
                ;;
            *)
                echo "Invalid choice. Try again."
                ;;
        esac
    done
}

main
