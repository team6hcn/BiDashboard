# Utiliser une image de base officielle de Python
FROM python:3.9-slim  

# Définir le répertoire de travail
WORKDIR /app  

# Installer les dépendances système
RUN apt-get update && apt-get install -y \  
    build-essential \  
    curl \  
    software-properties-common \  
    git \  
    && rm -rf /var/lib/apt/lists/*  

# Ajouter un alias pour Python et pip si nécessaire
RUN ln -s /usr/bin/python3 /usr/bin/python && \
    ln -s /usr/bin/pip3 /usr/bin/pip  

# Cloner le dépôt de l'application
RUN git clone https://github.com/team6hcn/BiDashboard.git .  

# Installer les dépendances Python
RUN pip install --no-cache-dir -r requirements.txt  

# Exposer le port Streamlit
EXPOSE 8501  

# Vérification de santé
HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health || exit 1  

# Point d'entrée pour exécuter l'application
ENTRYPOINT ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
