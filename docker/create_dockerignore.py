#!/usr/bin/env python
"""Script pour générer le fichier .dockerignore"""

content = """# Contrôle de version
.git
.gitignore
.github

# Environnement virtuel
.venv
venv
env
*env/

# Caches et fichiers temporaires
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
.pytest_cache
.coverage
htmlcov/
*.egg-info/
.installed.cfg
*.egg
.mypy_cache/

# Données volumineuses
data/
models/
outputs/
logs/
reports/

# Documentation et autres
docs/
summary/
benchmarking/results/
examples/outputs/

# Fichiers Docker (éviter les copies récursives)
Dockerfile*
docker-compose.yml
.dockerignore
docker/

# Divers
.DS_Store
.idea/
.vscode/
*.swp
*.swo
*~
.direnv/
.env
"""

with open('.dockerignore', 'w') as f:
    f.write(content)

print("Fichier .dockerignore créé avec succès.") 