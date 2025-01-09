#!/bin/bash

# Exit on error
set -e

echo "Setting up development environment..."

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install backend dependencies
echo "Installing backend dependencies..."
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Install frontend dependencies
echo "Installing frontend dependencies..."
cd Frontend
npm install

# Set up pre-commit hooks
echo "Setting up pre-commit hooks..."
cd ..
pre-commit install

# Create necessary directories
echo "Creating required directories..."
mkdir -p logs
mkdir -p monitoring/prometheus
mkdir -p monitoring/grafana/dashboards
mkdir -p monitoring/grafana/datasources

# Copy configuration files
echo "Copying configuration files..."
cp config/prometheus.yml monitoring/prometheus/
cp config/grafana/datasources/prometheus.yml monitoring/grafana/datasources/

# Set up environment variables
echo "Setting up environment variables..."
if [ ! -f ".env" ]; then
    cp .env.example .env
    echo "Created .env file from template. Please update with your settings."
fi

echo "Development environment setup complete!"
echo "To start the application:"
echo "1. Run 'docker-compose up' for infrastructure services"
echo "2. Run 'flask run' for the backend"
echo "3. Run 'npm start' in the Frontend directory for the frontend"
