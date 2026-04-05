#!/bin/bash
set -e
echo "=== Vanguard Setup ==="

if [ ! -f .env ]; then
  cp .env.example .env
  VAULT_KEY=$(python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())" 2>/dev/null || echo "")
  [ -n "$VAULT_KEY" ] && sed -i "s|VAULT_ENCRYPTION_KEY=|VAULT_ENCRYPTION_KEY=$VAULT_KEY|" .env
  echo "✅ Created .env"
fi

echo ""
echo "📋 Auth0 Setup (FREE — required for hackathon):"
echo "   1. Sign up at https://auth0.com/signup (free)"
echo "   2. Create an API with audience: vanguard-api"
echo "   3. Create a Single Page Application"
echo "   4. Create a Machine-to-Machine app for backend"
echo "   5. Enable Token Vault on your tenant"
echo "   6. Fill in AUTH0_DOMAIN, AUTH0_CLIENT_ID, AUTH0_CLIENT_SECRET in .env"
echo ""
echo "📋 OAuth Apps (FREE):"
echo "   Slack:  https://api.slack.com/apps → Create App → OAuth & Permissions"
echo "   GitHub: https://github.com/settings/developers → New OAuth App"
echo "   Add redirect URI: http://localhost:3000/api/connect/{service}/callback"
echo ""
echo "📦 Starting Ollama and pulling llama3.2 (free, runs locally)..."
docker compose up -d ollama
sleep 5
docker exec vanguard-ollama ollama pull llama3.2

echo ""
echo "✅ Ready. Run: docker compose up --build"
echo "   Then open: http://localhost:3000"
