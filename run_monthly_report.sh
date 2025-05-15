#!/bin/sh

# Script pour exécuter le rapport taxi mensuel avec débogage amélioré
# À programmer pour s'exécuter le 1er de chaque mois

# Définition des variables
BASE_DIR=$(dirname "$0")
BASE_DIR=$(cd "$BASE_DIR" && pwd)  # Obtenir le chemin absolu
SRC_DIR="${BASE_DIR}/scripts"
LOG_DIR="${BASE_DIR}/logs"
DATE_NOW=$(date +"%Y-%m")
LOG_FILE="${LOG_DIR}/rapport_${DATE_NOW}.log"

# Création du répertoire de logs s'il n'existe pas
mkdir -p "$LOG_DIR"

# Fonction pour enregistrer les messages avec horodatage
log() {
    TIMESTAMP=$(date +"%Y-%m-%d %H:%M:%S")
    echo "[${TIMESTAMP}] $1" | tee -a "$LOG_FILE"
}

# Début du traitement
log "🚀 Début de la génération du rapport mensuel"
log "📂 Répertoire de base: $BASE_DIR"
log "📂 Répertoire source: $SRC_DIR"

# Vérifier si les fichiers et dossiers nécessaires existent
if [ ! -d "$SRC_DIR" ]; then
    log "❌ Erreur: le répertoire src/ n'existe pas à $SRC_DIR"
    exit 1
fi

if [ ! -f "$SRC_DIR/automate_pipeline.py" ]; then
    log "❌ Erreur: le fichier automate_pipeline.py n'existe pas à $SRC_DIR/automate_pipeline.py"
    log "📂 Contenu de $SRC_DIR:"
    ls -la "$SRC_DIR" >> "$LOG_FILE" 2>&1
    exit 1
fi

# Vérifier si Python est installé et accessible
if ! command -v python >/dev/null 2>&1; then
    # Si 'python' n'est pas trouvé, essayons 'python3'
    if ! command -v python3 >/dev/null 2>&1; then
        log "❌ Erreur: ni python ni python3 n'ont été trouvés. Veuillez installer Python."
        exit 1
    else
        PYTHON_CMD="python3"
    fi
else
    PYTHON_CMD="python"
fi

log "🐍 Commande Python: $PYTHON_CMD"

# Aller dans le répertoire du projet
cd "$BASE_DIR" || {
    log "❌ Erreur: impossible d'accéder au répertoire $BASE_DIR"
    exit 1
}

# Récupération des données du mois précédent
log "📥 Récupération et préparation des données..."
log "💻 Exécution de: $PYTHON_CMD $SRC_DIR/automate_pipeline.py"

# Exécution avec capture détaillée de l'erreur
OUTPUT=$($PYTHON_CMD "$SRC_DIR/automate_pipeline.py" 2>&1)
EXIT_CODE=$?

# Enregistrer la sortie complète
echo "$OUTPUT" >> "$LOG_FILE"

# Vérification du succès
if [ $EXIT_CODE -eq 0 ]; then
    log "✅ Script Python exécuté avec succès"

    # Obtenir le mois du rapport depuis le fichier settings.yaml
    if [ -f "config/settings.yaml" ]; then
        MONTH=$(grep "report_month" config/settings.yaml | cut -d":" -f2 | tr -d ' ')
        REPORT_FILE="report-${MONTH}.html"

        log "✅ Rapport généré avec succès: $REPORT_FILE"
    else
        log "⚠️ Le fichier config/settings.yaml n'existe pas"
    fi
else
    log "❌ Erreur lors de l'exécution du script Python (code $EXIT_CODE)"
    log "📄 Détail de l'erreur:"
    log "$OUTPUT"
fi

log "🏁 Traitement terminé"