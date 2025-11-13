#!/bin/bash
set -e

echo "==================================="
echo "Initial Production Deployment"
echo "Server: 31.129.107.178"
echo "==================================="

NEW_SERVER="31.129.107.178"

echo ""
echo "Step 1: Starting database and redis..."
ssh root@$NEW_SERVER "cd /opt/budget-app && docker compose -f docker-compose.prod.yml up -d db redis"

echo ""
echo "Waiting for database to be ready..."
sleep 15

echo ""
echo "Step 2: Creating admin user..."
ssh root@$NEW_SERVER "cd /opt/budget-app && docker compose -f docker-compose.prod.yml exec -T db psql -U budget_user -d it_budget_db -c \"
CREATE TABLE IF NOT EXISTS departments (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    code VARCHAR(50),
    description TEXT,
    ftp_subdivision_name VARCHAR(255),
    default_category_id INTEGER,
    manager_name VARCHAR(255),
    contact_email VARCHAR(255),
    contact_phone VARCHAR(50),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Insert default department if not exists
INSERT INTO departments (name, code, description, is_active) 
VALUES ('IT Department', 'IT', 'Information Technology', true)
ON CONFLICT DO NOTHING;
\" || echo 'Database initialization done'"

echo ""
echo "Step 3: Checking container status..."
ssh root@$NEW_SERVER "cd /opt/budget-app && docker compose -f docker-compose.prod.yml ps"

echo ""
echo "==================================="
echo "Initial setup completed!"
echo "==================================="
echo ""
echo "Next steps:"
echo "1. Build and push Docker images via GitHub Actions"
echo "2. Pull images on server: docker compose pull"
echo "3. Start all services: docker compose up -d"
echo ""
echo "GitHub Secrets needed:"
echo "  PROD_HOST: 31.129.107.178"
echo "  PROD_USERNAME: root"
echo "  PROD_SSH_KEY: <your SSH private key>"
