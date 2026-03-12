#!/bin/bash
set -e

# DataPulse Development Deployment Script
# This script handles zero-downtime deployments to the dev environment

DEPLOY_DIR="/opt/datapulse"
BACKUP_DIR="/opt/datapulse-backup-$(date +%Y%m%d-%H%M%S)"
LOG_FILE="/var/log/datapulse-deploy.log"

# Logging function
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" | tee -a "$LOG_FILE"
}

# Error handling
handle_error() {
    log "❌ Deployment failed at step: $1"
    log "🔄 Rolling back to previous version..."

    if [ -d "$BACKUP_DIR" ]; then
        cd "$DEPLOY_DIR"
        docker compose down || true

        # Restore from backup
        rsync -av "$BACKUP_DIR/" "$DEPLOY_DIR/"
        docker compose --profile all up -d

        log "✅ Rollback completed"
    fi

    exit 1
}

# Main deployment function
deploy() {
    log "🚀 Starting DataPulse deployment..."

    # Step 1: Backup current deployment
    log "📦 Creating backup..."
    if [ -d "$DEPLOY_DIR" ]; then
        cp -r "$DEPLOY_DIR" "$BACKUP_DIR"
    fi

    # Step 2: Pull latest code
    log "📥 Pulling latest code from develop branch..."
    cd "$DEPLOY_DIR"
    git fetch origin || handle_error "git fetch"
    git checkout develop || handle_error "git checkout"
    git pull origin develop || handle_error "git pull"

    # Step 3: Refresh environment
    log "🔧 Refreshing environment variables..."
    source "$DEPLOY_DIR/scripts/refresh-env.sh" || handle_error "refresh env"

    # Step 4: Build new images
    log "🏗️ Building Docker images..."
    docker compose build --no-cache || handle_error "docker build"

    # Step 5: Stop old containers
    log "🛑 Stopping old containers..."
    docker compose down || true

    # Step 6: Start new containers
    log "🚀 Starting new containers..."
    docker compose --profile all up -d || handle_error "docker up"

    # Step 7: Wait for services
    log "⏳ Waiting for services to be ready..."
    sleep 30

    # Step 8: Health checks
    log "🏥 Running health checks..."

    # Check containers
    if ! docker compose ps | grep -q "Up"; then
        handle_error "containers not running"
    fi

    # Check backend health
    for i in {1..10}; do
        if curl -f http://localhost:8000/health > /dev/null 2>&1; then
            log "✅ Backend health check passed"
            break
        fi
        if [ $i -eq 10 ]; then
            handle_error "backend health check"
        fi
        sleep 5
    done

    # Check Streamlit
    for i in {1..10}; do
        if curl -f http://localhost:8501 > /dev/null 2>&1; then
            log "✅ Streamlit health check passed"
            break
        fi
        if [ $i -eq 10 ]; then
            log "⚠️ Streamlit health check failed (non-critical)"
        fi
        sleep 5
    done

    # Step 9: Cleanup old backup (keep last 3)
    log "🧹 Cleaning up old backups..."
    ls -dt /opt/datapulse-backup-* | tail -n +4 | xargs rm -rf || true

    log "🎉 Deployment completed successfully!"
    log "📊 Final service status:"
    docker compose ps | tee -a "$LOG_FILE"
}

# Run deployment
deploy
