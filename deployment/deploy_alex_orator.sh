#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to load environment variables from file
load_env() {
    if [ -f "$1" ]; then
        echo -e "${BLUE}📄 Loading configuration from $1...${NC}"
        export $(grep -v '^#' "$1" | grep -v '^$' | xargs)
        echo -e "${GREEN}✅ Configuration loaded${NC}"
    fi
}

# Function to check and install Docker
install_docker() {
    local ssh_cmd="$1"
    local remote_user="$2"
    local remote_host="$3"
    
    echo -e "${BLUE}🐳 Checking Docker installation...${NC}"
    
    $ssh_cmd $remote_user@$remote_host "
        if command -v docker >/dev/null 2>&1; then
            echo '✅ Docker is already installed'
            docker --version
        else
            echo '📦 Installing Docker...'
            
            # Update package index
            apt-get update -y >/dev/null 2>&1 || yum update -y >/dev/null 2>&1 || true
            
            # Install Docker using official script
            curl -fsSL https://get.docker.com -o get-docker.sh
            if [ -f get-docker.sh ]; then
                sh get-docker.sh
                rm get-docker.sh
                
                # Enable and start Docker service
                systemctl enable docker >/dev/null 2>&1 || true
                systemctl start docker >/dev/null 2>&1 || true
                
                # Add current user to docker group (if not root)
                if [ \"\$USER\" != \"root\" ]; then
                    usermod -aG docker \$USER >/dev/null 2>&1 || true
                fi
                
                # Verify installation
                if command -v docker >/dev/null 2>&1; then
                    echo '✅ Docker installed successfully'
                    docker --version
                else
                    echo '❌ Docker installation failed'
                    exit 1
                fi
            else
                echo '❌ Failed to download Docker installation script'
                exit 1
            fi
        fi
    "
    
    if [ $? -ne 0 ]; then
        echo -e "${RED}❌ Docker installation failed${NC}"
        exit 1
    fi
}

# Function to check and install docker-compose
install_docker_compose() {
    local ssh_cmd="$1"
    local remote_user="$2"
    local remote_host="$3"
    
    echo -e "${BLUE}🔧 Checking docker-compose installation...${NC}"
    
    $ssh_cmd $remote_user@$remote_host "
        # Check if docker-compose is already available
        if docker-compose --version >/dev/null 2>&1; then
            echo '✅ docker-compose is already installed'
            docker-compose --version
            exit 0
        fi
        
        # Check if docker compose plugin is available
        if docker compose version >/dev/null 2>&1; then
            echo '✅ Docker Compose plugin is available'
            docker compose version
            
            # Create compatibility symlink
            echo '🔗 Creating docker-compose compatibility link...'
            cat > /usr/local/bin/docker-compose << 'EOF'
#!/bin/bash
exec docker compose \"\$@\"
EOF
            chmod +x /usr/local/bin/docker-compose
            
            # Verify the symlink works
            if docker-compose --version >/dev/null 2>&1; then
                echo '✅ docker-compose compatibility link created successfully'
                docker-compose --version
            else
                echo '❌ Failed to create docker-compose compatibility link'
                exit 1
            fi
            exit 0
        fi
        
        # Neither docker-compose nor docker compose plugin available, install standalone version
        echo '📦 Installing docker-compose standalone...'
        
        # Get the latest stable version
        COMPOSE_VERSION=\"2.24.6\"
        ARCH=\$(uname -m)
        OS=\$(uname -s)
        
        # Download docker-compose
        echo \"📥 Downloading docker-compose v\$COMPOSE_VERSION for \$OS-\$ARCH...\"
        curl -L \"https://github.com/docker/compose/releases/download/v\$COMPOSE_VERSION/docker-compose-\$OS-\$ARCH\" -o /usr/local/bin/docker-compose
        
        if [ ! -f /usr/local/bin/docker-compose ]; then
            echo '❌ Failed to download docker-compose'
            exit 1
        fi
        
        # Make it executable
        chmod +x /usr/local/bin/docker-compose
        
        # Create symlink in /usr/bin for better PATH compatibility
        ln -sf /usr/local/bin/docker-compose /usr/bin/docker-compose 2>/dev/null || true
        
        # Verify installation
        if docker-compose --version >/dev/null 2>&1; then
            echo '✅ docker-compose installed successfully'
            docker-compose --version
        else
            echo '❌ docker-compose installation failed'
            echo 'Attempting to fix permissions and PATH...'
            
            # Try fixing permissions
            chmod 755 /usr/local/bin/docker-compose
            
            # Test again
            if /usr/local/bin/docker-compose --version >/dev/null 2>&1; then
                echo '✅ docker-compose fixed and working'
                /usr/local/bin/docker-compose --version
                
                # Add to PATH if needed
                if ! echo \$PATH | grep -q '/usr/local/bin'; then
                    echo 'export PATH=\"/usr/local/bin:\$PATH\"' >> /etc/environment
                    echo '📝 Added /usr/local/bin to PATH'
                fi
            else
                echo '❌ docker-compose still not working after fixes'
                ls -la /usr/local/bin/docker-compose
                file /usr/local/bin/docker-compose
                exit 1
            fi
        fi
    "
    
    if [ $? -ne 0 ]; then
        echo -e "${RED}❌ docker-compose installation failed${NC}"
        exit 1
    fi
}

# Function to verify Docker environment
verify_docker_environment() {
    local ssh_cmd="$1"
    local remote_user="$2"
    local remote_host="$3"
    
    echo -e "${BLUE}🔍 Verifying Docker environment...${NC}"
    
    $ssh_cmd $remote_user@$remote_host "
        echo '🐳 Docker version:'
        docker --version
        
        echo '📊 Docker system info:'
        docker info --format 'Version: {{.ServerVersion}}' 2>/dev/null || echo 'Docker daemon may not be running'
        
        echo '🔧 docker-compose version:'
        docker-compose --version
        
        echo '✅ Docker environment verification completed'
    "
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ Docker environment is ready${NC}"
    else
        echo -e "${RED}❌ Docker environment verification failed${NC}"
        exit 1
    fi
}

# Load deployment configuration
load_env "deploy.env"

# Default values (can be overridden by deploy.env or command line)
REMOTE_USER="${REMOTE_USER:-root}"
REMOTE_HOST="${REMOTE_HOST:-YOUR_SERVER_IP}"
SSH_KEY="${SSH_KEY_PATH:-~/.ssh/your_ssh_key}"
DEPLOY_BACKEND="${DEPLOY_BACKEND:-true}"
DEPLOY_BOT="${DEPLOY_BOT:-true}"
DEPLOY_WORKER="${DEPLOY_WORKER:-true}"
DEPLOY_DATABASES="${DEPLOY_DATABASES:-true}"
REMOTE_DEPLOY_DIR="${REMOTE_DEPLOY_DIR:-/opt/alex-orator-bot}"

# Usage function
usage() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Alex Orator Bot - Full Stack Deployment Script"
    echo ""
    echo "Configuration:"
    echo "  Create deploy.env file with your settings (see deploy.env.example)"
    echo "  Or use command line options to override defaults"
    echo ""
    echo "Options:"
    echo "  -u, --user USER     SSH username (default from deploy.env or 'root')"
    echo "  -h, --host HOST     Server hostname/IP (default from deploy.env or 'YOUR_SERVER_IP')"
    echo "  -k, --key PATH      SSH private key path (default from deploy.env or '~/.ssh/your_ssh_key')"
    echo "  --backend-only      Deploy only backend API"
    echo "  --bot-only          Deploy only Telegram bot"
    echo "  --worker-only       Deploy only message queue worker"
    echo "  --no-db            Skip database deployment"
    echo "  --help              Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0                               # Deploy using deploy.env configuration"
    echo "  $0 --backend-only                # Deploy only backend API"
    echo "  $0 --bot-only                    # Deploy only bot"
    echo "  $0 --worker-only                 # Deploy only message queue worker"
    echo "  $0 --no-db                       # Deploy without databases"
    echo "  $0 -h your-server.com -u ubuntu # Override server and user"
    echo ""
    echo "Configuration file (deploy.env):"
    echo "  REMOTE_HOST=your-server.com"
    echo "  REMOTE_USER=ubuntu"
    echo "  SSH_KEY_PATH=~/.ssh/your-key"
    echo "  APP_DB_PASSWORD=secure_db_password"
    echo "  JWT_SECRET_KEY=your-jwt-secret"
    echo "  SECRET_KEY=your-secret-key"
    echo "  TELEGRAM_TOKEN=your_bot_token"
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -u|--user)
            REMOTE_USER="$2"
            shift 2
            ;;
        -h|--host)
            REMOTE_HOST="$2"
            shift 2
            ;;
        -k|--key)
            SSH_KEY="$2"
            shift 2
            ;;
        --backend-only)
            DEPLOY_BACKEND=true
            DEPLOY_BOT=false
            DEPLOY_DATABASES=true
            shift
            ;;
        --bot-only)
            DEPLOY_BACKEND=false
            DEPLOY_BOT=true
            DEPLOY_WORKER=false
            DEPLOY_DATABASES=false
            shift
            ;;
        --worker-only)
            DEPLOY_BACKEND=false
            DEPLOY_BOT=false
            DEPLOY_WORKER=true
            DEPLOY_DATABASES=true
            shift
            ;;
        --no-db)
            DEPLOY_DATABASES=false
            shift
            ;;
        --help)
            usage
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            usage
            exit 1
            ;;
    esac
done

# Validate required configuration
if [ -z "$REMOTE_HOST" ]; then
    echo -e "${RED}❌ Error: REMOTE_HOST is required${NC}"
    echo -e "${RED}Set it in deploy.env file or use -h option${NC}"
    exit 1
fi

echo -e "${BLUE}🚀 Alex Orator Bot - Full Stack Deployment${NC}"
echo -e "${YELLOW}Target: $REMOTE_USER@$REMOTE_HOST${NC}"
echo -e "${YELLOW}SSH Key: $SSH_KEY${NC}"
echo -e "${YELLOW}Deploy Dir: $REMOTE_DEPLOY_DIR${NC}"
echo -e "${YELLOW}Databases: $([ "$DEPLOY_DATABASES" = true ] && echo "✅ Will deploy" || echo "⏭️  Skipped")${NC}"
echo -e "${YELLOW}Backend API: $([ "$DEPLOY_BACKEND" = true ] && echo "✅ Will deploy" || echo "⏭️  Skipped")${NC}"
echo -e "${YELLOW}Telegram Bot: $([ "$DEPLOY_BOT" = true ] && echo "✅ Will deploy" || echo "⏭️  Skipped")${NC}"
echo -e "${YELLOW}Message Queue Worker: $([ "$DEPLOY_WORKER" = true ] && echo "✅ Will deploy" || echo "⏭️  Skipped")${NC}"
echo ""

# Prepare SSH command with aggressive keep-alive settings
SSH_BASE_OPTIONS="-o ServerAliveInterval=30 -o ServerAliveCountMax=20 -o ConnectTimeout=60 -o TCPKeepAlive=yes"
SSH_CMD="ssh $SSH_BASE_OPTIONS"
if [ -n "$SSH_KEY" ] && [ "$SSH_KEY" != "" ]; then
    # Expand tilde in SSH key path and check if file exists
    SSH_KEY_EXPANDED=$(eval echo $SSH_KEY)
    if [ -f "$SSH_KEY_EXPANDED" ]; then
        SSH_CMD="ssh $SSH_BASE_OPTIONS -i $SSH_KEY_EXPANDED"
        echo -e "${YELLOW}Using SSH key: $SSH_KEY${NC}"
    else
        echo -e "${YELLOW}⚠️  SSH key not found: $SSH_KEY, using default SSH configuration${NC}"
        SSH_CMD="ssh $SSH_BASE_OPTIONS"
    fi
else
    echo -e "${YELLOW}Using default SSH configuration (no key specified)${NC}"
fi

# Prepare RSYNC command for file transfers
if [ -n "$SSH_KEY" ] && [ "$SSH_KEY" != "" ]; then
    SSH_KEY_EXPANDED=$(eval echo $SSH_KEY)
    if [ -f "$SSH_KEY_EXPANDED" ]; then
        RSYNC_CMD="rsync -e 'ssh $SSH_BASE_OPTIONS -i $SSH_KEY_EXPANDED'"
    else
        RSYNC_CMD="rsync -e 'ssh $SSH_BASE_OPTIONS'"
    fi
else
    RSYNC_CMD="rsync -e 'ssh $SSH_BASE_OPTIONS'"
fi

# Test SSH connection first
echo -e "${BLUE}🔐 Testing SSH connection...${NC}"
if ! $SSH_CMD -o ConnectTimeout=10 $REMOTE_USER@$REMOTE_HOST 'exit 0' 2>/dev/null; then
    echo -e "${RED}❌ SSH connection failed${NC}"
    echo -e "${RED}Please check:${NC}"
    echo -e "${RED}  - Server is accessible: $REMOTE_HOST${NC}"
    echo -e "${RED}  - User has access: $REMOTE_USER${NC}"
    if [ -n "$SSH_KEY" ]; then
        echo -e "${RED}  - SSH key exists: $SSH_KEY${NC}"
    else
        echo -e "${RED}  - SSH configuration and keys${NC}"
    fi
    exit 1
fi
echo -e "${GREEN}✅ SSH connection successful${NC}"

# Install and verify Docker environment
echo ""
install_docker "$SSH_CMD" "$REMOTE_USER" "$REMOTE_HOST"
install_docker_compose "$SSH_CMD" "$REMOTE_USER" "$REMOTE_HOST"
verify_docker_environment "$SSH_CMD" "$REMOTE_USER" "$REMOTE_HOST"
echo ""

# Check if .env file exists in project root
if [ ! -f "../.env" ]; then
    echo -e "${RED}❌ Root .env file not found${NC}"
    echo -e "${RED}Create .env file with required configuration${NC}"
    echo -e "${RED}See env.example for reference${NC}"
    exit 1
fi

# Clean existing deployments
echo -e "${BLUE}🧹 Cleaning existing deployments...${NC}"
$SSH_CMD $REMOTE_USER@$REMOTE_HOST "
    cd $REMOTE_DEPLOY_DIR 2>/dev/null || true
    docker-compose down --remove-orphans 2>/dev/null || true
    # Only remove stopped containers and dangling images (keep cache for faster builds)
    docker container prune -f 2>/dev/null || true
    docker image prune -f 2>/dev/null || true
    rm -rf $REMOTE_DEPLOY_DIR 2>/dev/null || true
    mkdir -p $REMOTE_DEPLOY_DIR
    
    # Create shared network for containers
    docker network create alex-orator-network 2>/dev/null || echo 'Network already exists'
" 2>/dev/null || true
echo -e "${GREEN}✅ Cleanup completed${NC}"
echo ""

# Copy project files (excluding development files)
echo -e "${BLUE}📁 Copying project files...${NC}"

# Check if .deployignore exists locally first
if [ -f "../.deployignore" ]; then
    echo -e "${YELLOW}📋 Using .deployignore exclusions...${NC}"
    if ! $RSYNC_CMD -av --exclude-from=../.deployignore ../ $REMOTE_USER@$REMOTE_HOST:$REMOTE_DEPLOY_DIR/; then
        echo -e "${YELLOW}⚠️  rsync with .deployignore failed, using basic exclusions${NC}"
        $RSYNC_CMD -av --exclude='.git' --exclude='__pycache__' --exclude='*.pyc' --exclude='node_modules' --exclude='.pytest_cache' --exclude='venv' --exclude='logs/*' ../ $REMOTE_USER@$REMOTE_HOST:$REMOTE_DEPLOY_DIR/
    fi
else
    echo -e "${YELLOW}⚠️  .deployignore not found, using basic exclusions${NC}"
    $RSYNC_CMD -av --exclude='.git' --exclude='__pycache__' --exclude='*.pyc' --exclude='node_modules' --exclude='.pytest_cache' --exclude='venv' --exclude='logs/*' ../ $REMOTE_USER@$REMOTE_HOST:$REMOTE_DEPLOY_DIR/
fi
echo -e "${GREEN}✅ Files copied${NC}"

# Configure for production
echo -e "${BLUE}⚙️  Configuring for production...${NC}"
$SSH_CMD $REMOTE_USER@$REMOTE_HOST "
    cd $REMOTE_DEPLOY_DIR
    
    # Update container names in docker-compose.yml
    sed -i 's/alex-orator-bot/alex-orator-bot/g' docker-compose.yml 2>/dev/null || true
    sed -i 's/alex-orator-network/alex-orator-network/g' docker-compose.yml 2>/dev/null || true
    
    # Set production environment
    sed -i 's/DEBUG=.*/DEBUG=false/' .env 2>/dev/null || true
    
    # Generate new secret keys for production if not set
    if command -v python3 >/dev/null 2>&1; then
        if ! grep -q 'SECRET_KEY=' .env || grep -q 'your-secret-key' .env; then
            NEW_SECRET=\$(python3 -c \"import secrets, base64; print(base64.b64encode(secrets.token_bytes(32)).decode())\")
            sed -i \"s/SECRET_KEY=.*/SECRET_KEY=\$NEW_SECRET/\" .env 2>/dev/null || true
        fi
        if ! grep -q 'JWT_SECRET_KEY=' .env || grep -q 'your-jwt-secret' .env; then
            NEW_JWT_SECRET=\$(python3 -c \"import secrets, base64; print(base64.b64encode(secrets.token_bytes(32)).decode())\")
            sed -i \"s/JWT_SECRET_KEY=.*/JWT_SECRET_KEY=\$NEW_JWT_SECRET/\" .env 2>/dev/null || true
        fi
    fi
    
    echo 'Production configuration completed'
"

# Deploy services
echo -e "${BLUE}🚀 Deploying services...${NC}"
$SSH_CMD $REMOTE_USER@$REMOTE_HOST "
    cd $REMOTE_DEPLOY_DIR
    
    # Create deployment profiles based on flags
    COMPOSE_PROFILES=''
    
    echo 'Building and starting services with timeout handling...'
    
    # Build with cache first (much faster)
    if ! timeout 600 docker-compose build; then
        echo 'Build failed with cache, trying without cache...'
        timeout 900 docker-compose build --no-cache
    fi
    
    # Start services based on deployment flags
    if [ '$DEPLOY_DATABASES' = true ] && [ '$DEPLOY_BACKEND' = true ] && [ '$DEPLOY_BOT' = true ] && [ '$DEPLOY_WORKER' = true ]; then
        echo 'Starting all services...'
        docker-compose up -d
    elif [ '$DEPLOY_DATABASES' = true ] && [ '$DEPLOY_BACKEND' = true ] && [ '$DEPLOY_WORKER' = true ]; then
        echo 'Starting databases, backend and worker...'
        docker-compose up -d app-db data-db backend worker
    elif [ '$DEPLOY_DATABASES' = true ] && [ '$DEPLOY_BACKEND' = true ]; then
        echo 'Starting databases and backend...'
        docker-compose up -d app-db data-db backend
    elif [ '$DEPLOY_BOT' = true ]; then
        echo 'Starting bot only...'
        docker-compose up -d telegram-bot
    elif [ '$DEPLOY_WORKER' = true ]; then
        echo 'Starting worker only...'
        docker-compose up -d app-db worker
    fi
    
    # Wait for services to be ready
    echo 'Waiting for services to start...'
    sleep 15
"

# Verify deployment
echo -e "${BLUE}🔍 Verifying deployment...${NC}"

if [ "$DEPLOY_BACKEND" = true ]; then
    echo -e "${YELLOW}Checking backend API...${NC}"
    for i in {1..30}; do
        if $SSH_CMD $REMOTE_USER@$REMOTE_HOST 'curl -s http://localhost:8000/health/ >/dev/null 2>&1'; then
            echo -e "${GREEN}✅ Backend API is ready!${NC}"
            break
        fi
        if [ $i -eq 30 ]; then
            echo -e "${RED}❌ Backend API health check failed${NC}"
            echo -e "${YELLOW}Checking backend logs:${NC}"
            $SSH_CMD $REMOTE_USER@$REMOTE_HOST "cd $REMOTE_DEPLOY_DIR && docker-compose logs --tail=20 backend"
            exit 1
        fi
        sleep 2
    done
fi

if [ "$DEPLOY_BOT" = true ]; then
    echo -e "${YELLOW}Checking Telegram bot...${NC}"
    if $SSH_CMD $REMOTE_USER@$REMOTE_HOST "cd $REMOTE_DEPLOY_DIR && docker-compose ps telegram-bot | grep -q 'Up'"; then
        echo -e "${GREEN}✅ Telegram Bot is running!${NC}"
    else
        echo -e "${RED}❌ Telegram Bot is not running${NC}"
        echo -e "${YELLOW}Checking bot logs:${NC}"
        $SSH_CMD $REMOTE_USER@$REMOTE_HOST "cd $REMOTE_DEPLOY_DIR && docker-compose logs --tail=20 telegram-bot"
        exit 1
    fi
fi

if [ "$DEPLOY_WORKER" = true ]; then
    echo -e "${YELLOW}Checking Message Queue Worker...${NC}"
    if $SSH_CMD $REMOTE_USER@$REMOTE_HOST "cd $REMOTE_DEPLOY_DIR && docker-compose ps worker | grep -q 'Up'"; then
        echo -e "${GREEN}✅ Message Queue Worker is running!${NC}"
    else
        echo -e "${RED}❌ Message Queue Worker is not running${NC}"
        echo -e "${YELLOW}Checking worker logs:${NC}"
        $SSH_CMD $REMOTE_USER@$REMOTE_HOST "cd $REMOTE_DEPLOY_DIR && docker-compose logs --tail=20 worker"
        exit 1
    fi
fi

# Final summary
echo ""
echo -e "${GREEN}🎉 Alex Orator Bot deployment completed successfully!${NC}"
echo ""
echo -e "${BLUE}📋 Your services are now running:${NC}"

if [ "$DEPLOY_DATABASES" = true ]; then
    echo -e "${YELLOW}💾 Databases:${NC}"
    echo -e "   • App DB: PostgreSQL on port 5432"
    echo -e "   • Data DB: PostgreSQL on port 5433"
fi

if [ "$DEPLOY_BACKEND" = true ]; then
    echo -e "${YELLOW}🔗 Backend API:${NC}"
    echo -e "   • API: http://$REMOTE_HOST:8000"
    echo -e "   • Docs: http://$REMOTE_HOST:8000/docs"
    echo -e "   • Health: http://$REMOTE_HOST:8000/health/"
fi

if [ "$DEPLOY_BOT" = true ]; then
    echo -e "${YELLOW}🤖 Telegram Bot:${NC}"
    echo -e "   • Status: Running and ready for messages"
    echo -e "   • Test: Send /start to your bot in Telegram"
fi

if [ "$DEPLOY_WORKER" = true ]; then
    echo -e "${YELLOW}⚙️  Message Queue Worker:${NC}"
    echo -e "   • Status: Running and processing message queue"
    echo -e "   • Processing: Messages from backend to Telegram users"
fi

echo ""
echo -e "${BLUE}📊 Useful commands:${NC}"
echo -e "${YELLOW}# Check all services status:${NC}"
echo "$SSH_CMD $REMOTE_USER@$REMOTE_HOST 'cd $REMOTE_DEPLOY_DIR && docker-compose ps'"

echo ""
echo -e "${YELLOW}# View logs:${NC}"
if [ "$DEPLOY_BACKEND" = true ] && [ "$DEPLOY_BOT" = true ] && [ "$DEPLOY_WORKER" = true ]; then
    echo "# All services logs:"
    echo "$SSH_CMD $REMOTE_USER@$REMOTE_HOST 'cd $REMOTE_DEPLOY_DIR && docker-compose logs -f'"
    echo ""
    echo "# Backend logs only:"
    echo "$SSH_CMD $REMOTE_USER@$REMOTE_HOST 'cd $REMOTE_DEPLOY_DIR && docker-compose logs -f backend'"
    echo ""
    echo "# Bot logs only:"
    echo "$SSH_CMD $REMOTE_USER@$REMOTE_HOST 'cd $REMOTE_DEPLOY_DIR && docker-compose logs -f telegram-bot'"
    echo ""
    echo "# Worker logs only:"
    echo "$SSH_CMD $REMOTE_USER@$REMOTE_HOST 'cd $REMOTE_DEPLOY_DIR && docker-compose logs -f worker'"
elif [ "$DEPLOY_BACKEND" = true ] && [ "$DEPLOY_WORKER" = true ]; then
    echo "# Backend and Worker logs:"
    echo "$SSH_CMD $REMOTE_USER@$REMOTE_HOST 'cd $REMOTE_DEPLOY_DIR && docker-compose logs -f backend worker'"
elif [ "$DEPLOY_BACKEND" = true ]; then
    echo "$SSH_CMD $REMOTE_USER@$REMOTE_HOST 'cd $REMOTE_DEPLOY_DIR && docker-compose logs -f backend'"
elif [ "$DEPLOY_BOT" = true ]; then
    echo "$SSH_CMD $REMOTE_USER@$REMOTE_HOST 'cd $REMOTE_DEPLOY_DIR && docker-compose logs -f telegram-bot'"
elif [ "$DEPLOY_WORKER" = true ]; then
    echo "$SSH_CMD $REMOTE_USER@$REMOTE_HOST 'cd $REMOTE_DEPLOY_DIR && docker-compose logs -f worker'"
fi

echo ""
echo -e "${YELLOW}# Restart services:${NC}"
echo "$SSH_CMD $REMOTE_USER@$REMOTE_HOST 'cd $REMOTE_DEPLOY_DIR && docker-compose restart'"

echo ""
echo -e "${YELLOW}# Stop services:${NC}"
echo "$SSH_CMD $REMOTE_USER@$REMOTE_HOST 'cd $REMOTE_DEPLOY_DIR && docker-compose down'"

echo ""
echo -e "${GREEN}🎯 Alex Orator Bot is ready for production use!${NC}"