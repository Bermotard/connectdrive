"""
Exceptions personnalisées pour l'application NetworkMounter.
"""

class NetworkMounterError(Exception):
    """Classe de base pour les exceptions de l'application."""
    pass

class MountError(NetworkMounterError):
    """Erreur lors du montage d'un partage réseau."""
    pass

class UnmountError(NetworkMounterError):
    """Erreur lors du démontage d'un partage réseau."""
    pass

class FstabError(NetworkMounterError):
    """Erreur liée à la manipulation du fichier fstab."""
    pass

class CredentialsError(NetworkMounterError):
    """Erreur liée à la gestion des identifiants."""
    pass

class ValidationError(NetworkMounterError):
    """Erreur de validation des données d'entrée."""
    pass
