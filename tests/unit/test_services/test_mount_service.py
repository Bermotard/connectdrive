"""
Tests unitaires pour le service de montage.
"""
import os
import pytest
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch, mock_open

from src.services.mount_service import MountService
from src.utils.exceptions import MountError


class TestMountService:
    """Tests pour le service de montage."""

    @pytest.fixture
    def mount_service(self):
        """Fixture pour créer une instance de MountService pour les tests."""
        with patch('src.services.mount_service.NetworkShareService'):
            return MountService()

    @pytest.fixture
    def mock_run_command(self):
        """Fixture pour mocker _run_sudo_command."""
        with patch.object(MountService, '_run_sudo_command') as mock:
            yield mock

    @pytest.fixture
    def mock_credentials(self):
        """Fixture pour mocker le gestionnaire d'identifiants."""
        with patch('src.services.mount_service.CredentialsManager') as mock:
            yield mock()

    def test_mount_share_success(self, mount_service, mock_run_command, mock_credentials):
        """Test le montage réussi d'un partage réseau."""
        # Configuration des mocks
        mock_run_command.return_value = (True, "")
        mock_credentials.get_credentials.return_value = {'username': 'user', 'password': 'pass'}
        
        # Appel de la méthode à tester
        result = mount_service.mount_share(
            share_path="//server/share",
            mount_point="/mnt/point",
            username='user',
            password='pass',
            domain='WORKGROUP',
            mount_options='rw,vers=3.0'
        )
        
        # Vérifications
        assert result is True
        mock_run_command.assert_called_once()
        mock_credentials.save_credentials.assert_called_once()

    def test_mount_share_failure(self, mount_service, mock_run_command):
        """Test l'échec du montage d'un partage réseau."""
        # Configuration du mock pour simuler une erreur
        mock_run_command.return_value = (False, "Mount error")
        
        # Test et vérifications
        with pytest.raises(MountError):
            mount_service.mount_share(
                share_path="//invalid/share",
                mount_point="/invalid/mount",
                username='user',
                password='pass'
            )

    def test_unmount_share_success(self, mount_service, mock_run_command):
        """Test le démontage réussi d'un partage."""
        # Configuration du mock
        mock_run_command.return_value = (True, "")
        
        # Appel de la méthode à tester
        result = mount_service.unmount_share("/mnt/point")
        
        # Vérifications
        assert result is True
        mock_run_command.assert_called_once()

    def test_list_mounted_shares(self, mount_service, mock_run_command):
        """Test la liste des partages montés."""
        # Configuration du mock
        mock_output = "//server/share on /mnt/point type cifs (rw,relatime,vers=3.0)"
        mock_run_command.return_value = (True, mock_output)
        
        # Appel de la méthode à tester
        result = mount_service.list_mounted_shares()
        
        # Vérifications
        assert len(result) == 1
        assert "//server/share" in result[0]
        assert "/mnt/point" in result[0]

    def test_run_sudo_command_no_root(self, mount_service):
        """Test l'exécution d'une commande sudo sans être root."""
        with patch('os.geteuid', return_value=1000), \
             patch('subprocess.run') as mock_run:
            
            mock_run.return_value = MagicMock(returncode=0, stdout="output")
            mock_tk = MagicMock()
            
            # Appel de la méthode à tester
            success, output = mount_service._run_sudo_command(
                ["ls", "/root"],
                parent_window=mock_tk
            )
            
            # Vérifications
            assert success is True
            assert output == "output"
            mock_run.assert_called_once()

    def test_run_sudo_command_as_root(self, mount_service):
        """Test l'exécution d'une commande sudo en étant root."""
        with patch('os.geteuid', return_value=0), \
             patch('subprocess.run') as mock_run:
            
            mock_run.return_value = MagicMock(returncode=0, stdout="root output")
            
            # Appel de la méthode à tester
            success, output = mount_service._run_sudo_command(["ls", "/root"])
            
            # Vérifications
            assert success is True
            assert output == "root output"
            mock_run.assert_called_once()

    def test_run_sudo_command_error(self, mount_service):
        """Test la gestion des erreurs dans _run_sudo_command."""
        with patch('os.geteuid', return_value=0), \
             patch('subprocess.run') as mock_run:
            
            mock_run.side_effect = subprocess.CalledProcessError(1, "cmd", "error")
            
            # Appel de la méthode à tester
            success, output = mount_service._run_sudo_command(["invalid-command"])
            
            # Vérifications
            assert success is False
            assert "error" in output

    def test_mount_with_invalid_credentials(self, mount_service, mock_credentials):
        """Test le montage avec des identifiants invalides."""
        mock_credentials.get_credentials.return_value = None
        
        with pytest.raises(ValueError):
            mount_service.mount_share(
                share_path="//server/share",
                mount_point="/mnt/point"
            )

    def test_unmount_non_existent_share(self, mount_service, mock_run_command):
        """Test le démontage d'un partage non monté."""
        mock_run_command.return_value = (False, "Not mounted")
        
        with pytest.raises(MountError):
            mount_service.unmount_share("/non/existent/mount")

    def test_list_empty_mounts(self, mount_service, mock_run_command):
        """Test la liste des partages quand aucun n'est monté."""
        mock_run_command.return_value = (True, "")
        
        result = mount_service.list_mounted_shares()
        assert len(result) == 0

    def test_mount_with_special_characters(self, mount_service, mock_run_command, mock_credentials):
        """Test le montage avec des caractères spéciaux dans les chemins."""
        mock_run_command.return_value = (True, "")
        mock_credentials.get_credentials.return_value = {'username': 'user@domain', 'password': 'p@ssw0rd#'}
        
        result = mount_service.mount_share(
            share_path="//sérvèr/p@th",
            mount_point="/mnt/point spécial",
            username='user@domain',
            password='p@ssw0rd#'
        )
        
        assert result is True
        mock_run_command.assert_called_once()

    def test_mount_without_required_parameters(self, mount_service):
        """Test le montage sans paramètres requis."""
        with pytest.raises(ValueError):
            mount_service.mount_share(share_path=None, mount_point="/mnt/point")
            
        with pytest.raises(ValueError):
            mount_service.mount_share(share_path="//server/share", mount_point=None)

    def test_cleanup_on_mount_failure(self, mount_service, mock_run_command, mock_credentials):
        """Test le nettoyage en cas d'échec du montage."""
        # Simuler un échec après la création du fichier d'identifiants
        mock_run_command.side_effect = [
            (True, ""),  # Création du répertoire
            (False, "Mount failed")  # Échec du montage
        ]
        
        with patch('os.path.exists', return_value=True), \
             patch('os.remove') as mock_remove, \
             pytest.raises(MountError):
            
            mount_service.mount_share(
                share_path="//server/share",
                mount_point="/mnt/point",
                username='user',
                password='pass'
            )
            
            # Vérifier que le fichier temporaire a été supprimé
            mock_remove.assert_called_once()

    def test_multiple_mounts(self, mount_service, mock_run_command, mock_credentials):
        """Test plusieurs montages successifs."""
        mock_run_command.return_value = (True, "")
        mock_credentials.get_credentials.return_value = {'username': 'user', 'password': 'pass'}
        
        # Premier montage
        result1 = mount_service.mount_share("//server/share1", "/mnt/point1", 'user', 'pass')
        assert result1 is True
        
        # Deuxième montage
        result2 = mount_service.mount_share("//server/share2", "/mnt/point2", 'user', 'pass')
        assert result2 is True
        
        # Vérifier que les deux commandes ont été appelées
        assert mock_run_command.call_count == 2
