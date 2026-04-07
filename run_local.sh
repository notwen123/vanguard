#!/bin/bash
set -e

echo "🚀 Starting Vanguard - Local Launch (No Docker)"

# 1. Setup Backend
echo "📦 Setting up Backend..."
cd backend
python3 -m venv venv
source venv/bin/activate
python3 -m pip install --upgrade pip
python3 -m pip install -r requirements.txt
echo "✅ Backend Ready"

# 2. Setup Frontend
echo "📦 Setting up Frontend..."
cd ../frontend
npm install
echo "✅ Frontend Ready"

# 3. Pull Ollama Model
echo "🧠 Ensuring Llama 3.2 is available in Ollama..."
ollama pull llama3.2 || echo "⚠️ Could not pull llama3.2 automatically. Ensure Ollama is running."

echo "--------------------------------------------------"
echo "✅ SETUP COMPLETE"
echo "--------------------------------------------------"
echo "To run the project, open TWO terminals:"
echo ""
echo "Terminal 1 (Backend):"
echo "cd backend && source venv/bin/activate && python3 -m uvicorn app.main:app --reload"
echo ""
echo "Terminal 2 (Frontend):"
echo "cd frontend && npm run dev"
echo "--------------------------------------------------"
