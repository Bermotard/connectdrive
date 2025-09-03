"""
Configuration des fixtures et hooks pytest pour les tests.
"""
import os
import sys
from pathlib import Path

# Ajout du répertoire racine au PYTHONPATH
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest

# Configuration des fixtures communes ici
@pytest.fixture(scope="session")
def test_data_dir():
    """Retourne le chemin vers le répertoire de données de test."""
    return Path(__file__).parent / "data"

# Configuration pour les tests d'intégration
@pytest.fixture(scope="module")
def integration_config():
    """Configuration pour les tests d'intégration."""
    return {
        "test_timeout": 30,  # secondes
        "max_retries": 3,
    }
