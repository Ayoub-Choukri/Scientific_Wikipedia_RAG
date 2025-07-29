#!/bin/bash

# Lancer Ollama en arrière-plan, rediriger sa sortie dans un fichier
ollama serve > /tmp/ollama.log 2>&1 &
OLLAMA_PID=$!

# Afficher la sortie de ollama serve en *temps réel* dans la console, en parallèle
tail -f /tmp/ollama.log &
TAIL_PID=$!

# Attendre que le serveur soit prêt
echo "⏳ Attente du démarrage d'Ollama..."
for i in {1..20}; do
  if curl -s http://localhost:11434 > /dev/null; then
    echo "✅ Ollama est prêt"
    break
  fi
  sleep 1
done

# Pull des modèles
ollama pull llama3.1:8b
ollama pull llama3.2:1b


echo "📦 Models downladed"


# (Optionnel) arrêter le serveur Ollama si tu veux le relancer autrement
# kill $OLLAMA_PID
# kill $TAIL_PID

# Lancer ton app Flask (remplace exec si tu veux que python soit le processus principal)
exec python -u /app/Webapp/Api_Webapp_Files/Api_Webapp.py

