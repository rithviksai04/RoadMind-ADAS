#!/usr/bin/env bash
# Downloads US Accidents (Moosavi et al.) via the Kaggle API.
# Credentials: put your own kaggle.json in ~/.kaggle/ (chmod 600) or export
# KAGGLE_USERNAME / KAGGLE_KEY. Nothing is hardcoded here.
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p data/raw
.venv/bin/kaggle datasets download -d sobhanmoosavi/us-accidents -p data/raw --unzip
ls -lh data/raw
