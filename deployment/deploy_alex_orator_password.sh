#!/usr/bin/env bash
# Alex Orator Bot — Deploy (rsync + docker compose v2/v1) — Password Authentication
# Копия скрипта для подключения по логину и паролю

set -euo pipefail

BLUE='\033[0;34m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# ---------------- Paths ----------------
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$SCRIPT_DIR"
if [ -f "$SCRIPT_DIR/../docker-compose.yml" ] || [ -f "$SCRIPT_DIR/../compose.yaml" ] || [ -f "$SCRIPT_DIR/../compose.yml" ]; then
  PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
fi

# ---------------- Env loader (no export $(grep ...)) ----------------
load_env() {
  local env_file="$SCRIPT_DIR/deploy_password.env"
  if [ ! -f "$env_file" ]; then
    echo -e "${RED}❌ deploy_password.env not found at $env_file${NC}"
    exit 1
  fi
  set -o allexport
  # shellcheck disable=SC1090
  . "$env_file"
  set +o allexport

  : "${REMOTE_HOST?}"; : "${REMOTE_USER?}"; : "${REMOTE_PASSWORD?}"; : "${REMOTE_DEPLOY_DIR?}"

  : "${DEPLOY_DATABASES:=true}"
  : "${DEPLOY_BACKEND:=true}"
  : "${DEPLOY_BOT:=true}"
  : "${DEPLOY_WORKER:=true}"   # включил по умолчанию, чтобы воркер тоже катался
  : "${DEPLOY_ADMIN_PANEL:=false}"   # админ-панель по умолчанию отключена для безопасности
}

# ---------------- SSH helper with password ----------------
SSH_CMD="ssh -o StrictHostKeyChecking=no -o PreferredAuthentications=password -o PubkeyAuthentication=no"
prepare_ssh() {
  echo -e "${YELLOW}🔑 Using password authentication for ${REMOTE_USER}@${REMOTE_HOST}${NC}"
  echo -e "${YELLOW}⚠️  Make sure sshpass is installed: sudo apt-get install sshpass${NC}"
  
  # Check if sshpass is available
  if ! command -v sshpass >/dev/null 2>&1; then
    echo -e "${RED}❌ sshpass not found. Install it with: sudo apt-get install sshpass${NC}"
    exit 1
  fi
  
  # Test connection first
  echo -e "${BLUE}🔍 Testing SSH connection...${NC}"
  if sshpass -p "$REMOTE_PASSWORD" ssh -o StrictHostKeyChecking=no -o PreferredAuthentications=password -o PubkeyAuthentication=no -o ConnectTimeout=10 "${REMOTE_USER}@${REMOTE_HOST}" "echo 'SSH connection successful'" 2>/dev/null; then
    echo -e "${GREEN}✅ SSH connection test passed${NC}"
  else
    echo -e "${RED}❌ SSH connection test failed${NC}"
    echo -e "${YELLOW}💡 Try manual connection: ssh ${REMOTE_USER}@${REMOTE_HOST}${NC}"
    exit 1
  fi
  
  SSH_CMD="sshpass -p $REMOTE_PASSWORD ssh -o StrictHostKeyChecking=no -o PreferredAuthentications=password -o PubkeyAuthentication=no"
}

# ---------------- Detect local compose file ----------------
LOCAL_COMPOSE_FILE=""
set_local_compose_file() {
  if   [ -f "$PROJECT_ROOT/docker-compose.yml" ]; then LOCAL_COMPOSE_FILE="$PROJECT_ROOT/docker-compose.yml"
  elif [ -f "$PROJECT_ROOT/compose.yaml" ];      then LOCAL_COMPOSE_FILE="$PROJECT_ROOT/compose.yaml"
  elif [ -f "$PROJECT_ROOT/compose.yml" ];       then LOCAL_COMPOSE_FILE="$PROJECT_ROOT/compose.yml"
  else
    echo -e "${RED}❌ No compose file found in $PROJECT_ROOT (docker-compose.yml / compose.yaml)${NC}"
    exit 1
  fi
  echo -e "${BLUE}🧩 Using local compose: $LOCAL_COMPOSE_FILE${NC}"
}

# ---------------- Sync files to remote ----------------
sync_files() {
  echo -e "${BLUE}📤 Syncing to ${REMOTE_USER}@${REMOTE_HOST}:${REMOTE_DEPLOY_DIR} ...${NC}"
  $SSH_CMD "${REMOTE_USER}@${REMOTE_HOST}" "mkdir -p '$REMOTE_DEPLOY_DIR'"

  # Create temporary archive
  local temp_archive="/tmp/alex-orator-deploy-$(date +%s).tar.gz"
  echo -e "${BLUE}📦 Creating archive...${NC}"
  
  # Create archive with necessary files
  tar -czf "$temp_archive" \
    -C "$PROJECT_ROOT" \
    docker-compose.yml \
    deployment/ \
    backend/ \
    telegram-bot/ \
    worker/ \
    admin-panel/ \
    2>/dev/null || true

  # Transfer archive
  echo -e "${BLUE}📤 Transferring archive...${NC}"
  sshpass -p "$REMOTE_PASSWORD" scp -o StrictHostKeyChecking=no -o PreferredAuthentications=password -o PubkeyAuthentication=no \
    "$temp_archive" "${REMOTE_USER}@${REMOTE_HOST}:/tmp/"

  # Extract on remote server
  echo -e "${BLUE}📂 Extracting on remote server...${NC}"
  $SSH_CMD "${REMOTE_USER}@${REMOTE_HOST}" "\
    cd '$REMOTE_DEPLOY_DIR' && \
    tar -xzf /tmp/$(basename $temp_archive) && \
    rm -f /tmp/$(basename $temp_archive) && \
    if [ -f deployment/deploy.env ]; then \
      cp -f deployment/deploy.env .env; \
      if command -v sed >/dev/null 2>&1; then \
        sed -i -E 's/^([A-Za-z_][A-Za-z0-9_]*)=\"(.*)\"$/\1=\2/' .env || true; \
      fi; \
    fi"

  # Clean up local archive
  rm -f "$temp_archive"

  echo -e "${GREEN}✅ Files synced${NC}"
}

# ---------------- Remote helpers ----------------
service_exists_remote() {
  local svc="$1"
  local REMOTE_COMPOSE_FILE="${REMOTE_DEPLOY_DIR}/docker-compose.yml"
  local REMOTE_ENV_FILE="${REMOTE_DEPLOY_DIR}/.env"

  $SSH_CMD "${REMOTE_USER}@${REMOTE_HOST}" bash -lc "
    set -e
    if command -v docker >/dev/null 2>&1 && docker compose version >/dev/null 2>&1; then
      docker compose --env-file '$REMOTE_ENV_FILE' -f '$REMOTE_COMPOSE_FILE' config --services | grep -x '$svc' >/dev/null
    elif command -v docker-compose >/dev/null 2>&1 || [ -x /usr/local/bin/docker-compose ]; then
      docker-compose --env-file '$REMOTE_ENV_FILE' -f '$REMOTE_COMPOSE_FILE' config --services | grep -x '$svc' >/dev/null
    else
      exit 1
    fi
  "
}

remote_compose() {
  local CMD_ARGS="$*"
  local REMOTE_COMPOSE_FILE="${REMOTE_DEPLOY_DIR}/docker-compose.yml"
  local REMOTE_ENV_FILE="${REMOTE_DEPLOY_DIR}/.env"

  $SSH_CMD "${REMOTE_USER}@${REMOTE_HOST}" bash -lc "
    set -e
    if command -v docker >/dev/null 2>&1 && docker compose version >/dev/null 2>&1; then
      docker compose --env-file '$REMOTE_ENV_FILE' -f '$REMOTE_COMPOSE_FILE' $CMD_ARGS
    elif command -v docker-compose >/dev/null 2>&1 || [ -x /usr/local/bin/docker-compose ]; then
      docker-compose --env-file '$REMOTE_ENV_FILE' -f '$REMOTE_COMPOSE_FILE' $CMD_ARGS
    else
      echo 'docker compose not found' >&2; exit 127
    fi
  "
}

# Correct service names from docker-compose.yml
SVC_DB="app-db"
SVC_BACKEND="backend"
SVC_BOT="telegram-bot"
SVC_WORKER="worker"
SVC_ADMIN_PANEL="admin-panel"

compose_up_if_exists() {
  local svc="$1"
  if service_exists_remote "$svc"; then
    echo -e "${YELLOW}⬆️  Up (rebuild): $svc${NC}"
    remote_compose up -d --build "$svc" || true
  else
    echo -e "${YELLOW}ℹ️  Skip: service '$svc' not found in compose${NC}"
  fi
}

compose_ps()      { remote_compose ps; }
compose_logs()    { remote_compose logs -f "$@"; }
compose_restart() { remote_compose restart "$@"; }
compose_down()    { remote_compose down; }

# ---------------- Main ----------------
main() {
  load_env
  prepare_ssh
  set_local_compose_file

  echo -e "${BLUE}🔑 Target: ${REMOTE_USER}@${REMOTE_HOST}${NC}"
  echo -e "${BLUE}📁 Remote dir: ${REMOTE_DEPLOY_DIR}${NC}"
  echo -e "${BLUE}⚙️  Plan: DB=${DEPLOY_DATABASES} BACKEND=${DEPLOY_BACKEND} BOT=${DEPLOY_BOT} WORKER=${DEPLOY_WORKER} ADMIN_PANEL=${DEPLOY_ADMIN_PANEL}${NC}"

  $SSH_CMD "${REMOTE_USER}@${REMOTE_HOST}" "mkdir -p '$REMOTE_DEPLOY_DIR'"

  if [ "$DEPLOY_DATABASES" = "true" ]; then
    sync_files
    compose_up_if_exists "$SVC_DB"
  fi

  if [ "$DEPLOY_BACKEND" = "true" ]; then
    sync_files
    compose_up_if_exists "$SVC_BACKEND"
  fi

  if [ "$DEPLOY_BOT" = "true" ]; then
    sync_files
    compose_up_if_exists "$SVC_BOT"
  fi

  if [ "$DEPLOY_WORKER" = "true" ]; then
    sync_files
    compose_up_if_exists "$SVC_WORKER"
  fi

  if [ "$DEPLOY_ADMIN_PANEL" = "true" ]; then
    sync_files
    compose_up_if_exists "$SVC_ADMIN_PANEL"
  fi

  echo -e "${BLUE}📋 Status:${NC}"
  compose_ps || true

  echo -e "${GREEN}🚀 Deployment complete${NC}"
}

main "$@"
