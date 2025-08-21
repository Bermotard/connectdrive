"""
Module de journalisation pour l'application NetworkMounter.
"""
import logging
import logging.handlers
from pathlib import Path
import os
from typing import Optional

def setup_logger(name: str = "network_mounter", log_level: int = logging.INFO) -> logging.Logger:
    """
    Configure et retourne un logger.
    
    Args:
        name: Nom du logger
        log_level: Niveau de journalisation (par défaut: INFO)
        
    Returns:
        Instance du logger configuré
    """
    # Créer le logger
    logger = logging.getLogger(name)
    logger.setLevel(log_level)
    
    # Créer le formateur
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Créer le gestionnaire de console
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    
    # Créer le répertoire de logs s'il n'existe pas
    log_dir = Path.home() / ".network_mounter" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # Créer le gestionnaire de fichier rotatif
    log_file = log_dir / "network_mounter.log"
    file_handler = logging.handlers.RotatingFileHandler(
        log_file,
        maxBytes=5*1024*1024,  # 5 Mo
        backupCount=3,
        encoding='utf-8'
    )
    file_handler.setFormatter(formatter)
    
    # Ajouter les gestionnaires au logger
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    
    return logger

def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Retourne un logger configuré.
    
    Args:
        name: Nom du logger (optionnel)
        
    Returns:
        Instance du logger
    """
    return logging.getLogger(name or "network_mounter")
