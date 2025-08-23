"""
Exceptions personnalisées pour l'application NetworkMounter.
"""

class NetworkMounterError(Exception):
    """Classe de base pour les exceptions de l'application."""
    pass

class MountError(NetworkMounterError):
    """Error while mounting a network share."""
    pass

class UnmountError(NetworkMounterError):
    """Error while unmounting a network share."""
    pass

class FstabError(NetworkMounterError):
    """Error related to fstab file manipulation."""
    pass

class CredentialsError(NetworkMounterError):
    """Error related to credentials management."""
    pass

class ValidationError(NetworkMounterError):
    """Input data validation error."""
    pass
