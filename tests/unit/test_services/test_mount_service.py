"""
Tests unitaires pour le service de montage.
"""
import subprocess
from unittest.mock import MagicMock, patch

import pytest

from src.services.mount_service import MountService
from src.utils.exceptions import MountError


class TestMountService:
    """Tests pour le service de montage."""

    @pytest.fixture
    def mock_credentials(self):
        """Fixture pour mocker le gestionnaire d'identifiants."""
        with patch('src.services.mount_service.CredentialsManager') as mock:
            yield mock()

    @pytest.fixture
    def mock_run_command(self):
        """Fixture pour mocker _run_sudo_command."""
        with patch.object(MountService, '_run_sudo_command') as mock:
            yield mock

    @pytest.fixture
    def mount_service(self, mock_credentials):
        """Fixture pour créer une instance de MountService pour les tests.

        Dépend de mock_credentials pour que le service soit instancié avec
        le gestionnaire d'identifiants mocké (pas d'accès au filesystem).
        """
        with patch('src.services.mount_service.NetworkShareService'):
            yield MountService()

    @pytest.fixture
    def mock_fs_ops(self):
        """Mocke les opérations filesystem pour ne pas toucher au vrai système."""
        with patch('src.services.mount_service.os.makedirs') as mock_makedirs, \
             patch('src.services.mount_service.os.chmod') as mock_chmod:
            yield mock_makedirs, mock_chmod

    @pytest.fixture
    def mock_ismount(self):
        """Mocke os.path.ismount."""
        with patch('src.services.mount_service.os.path.ismount') as mock:
            yield mock

    def test_mount_share_success(self, mount_service, mock_run_command, mock_credentials, mock_fs_ops):
        """Test le montage réussi d'un partage réseau avec identifiants."""
        mock_run_command.return_value = (True, "")

        result = mount_service.mount_share(
            server="server",
            share="share",
            mount_point="/mnt/point",
            username="user",
            password="pass",
            domain="WORKGROUP",
            options="rw,vers=3.0"
        )

        assert result == (True, "Share share successfully mounted on /mnt/point")
        mock_run_command.assert_called_once()
        mock_credentials.create_credentials_file.assert_called_once_with(
            username="user",
            password="pass",
            domain="WORKGROUP",
            share_name="share",
            server="server"
        )
        # Le fichier d'identifiants est suivi pour nettoyage ultérieur
        assert mount_service.active_credentials["/mnt/point"] == mock_credentials.create_credentials_file.return_value

    def test_mount_share_without_credentials(self, mount_service, mock_run_command, mock_credentials, mock_fs_ops):
        """Test le montage sans identifiants (partage invité)."""
        mock_run_command.return_value = (True, "")

        result = mount_service.mount_share(
            server="server",
            share="share",
            mount_point="/mnt/point"
        )

        assert result[0] is True
        mock_credentials.create_credentials_file.assert_not_called()

    def test_mount_share_failure(self, mount_service, mock_run_command, mock_fs_ops):
        """Test l'échec du montage d'un partage réseau."""
        mock_run_command.return_value = (False, "Mount error")

        result = mount_service.mount_share(
            server="invalid",
            share="share",
            mount_point="/mnt/point"
        )

        assert result == (False, "Mount error")

    def test_mount_share_custom_options(self, mount_service, mock_run_command, mock_fs_ops):
        """Test que les options personnalisées sont appliquées à la commande."""
        mock_run_command.return_value = (True, "")

        mount_service.mount_share(
            server="server",
            share="share",
            mount_point="/mnt/point",
            options="vers=2.0,sec=ntlm"
        )

        cmd = mock_run_command.call_args[0][0]
        opt_idx = cmd.index("-o")
        assert "vers=2.0" in cmd[opt_idx + 1]
        assert "sec=ntlm" in cmd[opt_idx + 1]
        # Les options par défaut CIFS ne doivent pas être ajoutées
        assert "x-systemd.automount" not in cmd[opt_idx + 1]

    def test_mount_share_cifs_defaults(self, mount_service, mock_run_command, mock_fs_ops):
        """Test que les options par défaut CIFS sont utilisées sans options fournies."""
        mock_run_command.return_value = (True, "")

        mount_service.mount_share(
            server="server",
            share="share",
            mount_point="/mnt/point",
            filesystem="cifs"
        )

        cmd = mock_run_command.call_args[0][0]
        opt_idx = cmd.index("-o")
        assert "vers=3.0" in cmd[opt_idx + 1]
        assert "x-systemd.automount" in cmd[opt_idx + 1]
        assert cmd[cmd.index("-t") + 1] == "cifs"
        assert cmd[-2] == "//server/share"
        assert cmd[-1] == "/mnt/point"

    def test_mount_share_nfs(self, mount_service, mock_run_command, mock_fs_ops):
        """Test le montage d'un partage NFS."""
        mock_run_command.return_value = (True, "")

        mount_service.mount_share(
            server="192.168.1.10",
            share="/export/data",
            mount_point="/mnt/data",
            filesystem="nfs"
        )

        cmd = mock_run_command.call_args[0][0]
        assert cmd[cmd.index("-t") + 1] == "nfs"
        assert cmd[-2] == "192.168.1.10:/export/data"

    def test_mount_share_makedirs_failure(self, mount_service, mock_run_command):
        """Test le retour d'erreur si le point de montage ne peut pas être créé."""
        with patch('src.services.mount_service.os.makedirs', side_effect=OSError("denied")):
            result = mount_service.mount_share(
                server="server",
                share="share",
                mount_point="/mnt/point"
            )

        assert result[0] is False
        assert "Failed to create mount point" in result[1]
        mock_run_command.assert_not_called()

    def test_unmount_share_success(self, mount_service, mock_run_command, mock_ismount):
        """Test le démontage réussi d'un partage."""
        mock_ismount.return_value = True
        mock_run_command.return_value = (True, "")

        result = mount_service.unmount_share("/mnt/point")

        assert result == (True, "Successfully unmounted /mnt/point")
        mock_run_command.assert_called_once()
        cmd = mock_run_command.call_args[0][0]
        assert cmd[0] == "umount"
        assert cmd[-1] == "/mnt/point"

    def test_unmount_not_a_mount_point(self, mount_service, mock_run_command, mock_ismount):
        """Test le démontage d'un chemin qui n'est pas un point de montage."""
        mock_ismount.return_value = False

        result = mount_service.unmount_share("/mnt/nonexistent")

        assert result[0] is False
        assert "not a mount point" in result[1]
        mock_run_command.assert_not_called()

    def test_unmount_force_and_lazy(self, mount_service, mock_run_command, mock_ismount):
        """Test le démontage forcé et différé."""
        mock_ismount.return_value = True
        mock_run_command.return_value = (True, "")

        mount_service.unmount_share("/mnt/point", force=True, lazy=True)

        cmd = mock_run_command.call_args[0][0]
        assert cmd == ["umount", "-f", "-l", "/mnt/point"]

    def test_list_mounts_success(self, mount_service):
        """Test la liste des montages actifs."""
        with patch('src.services.mount_service.subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="//server/share on /mnt/point type cifs")

            success, output = mount_service.list_mounts()

        assert success is True
        assert "//server/share" in output
        mock_run.assert_called_once()
        assert mock_run.call_args[0][0] == ["mount"]

    def test_list_mounts_error(self, mount_service):
        """Test la gestion d'erreur de la liste des montages."""
        with patch('src.services.mount_service.subprocess.run') as mock_run:
            mock_run.side_effect = subprocess.CalledProcessError(1, "mount", stderr="permission denied")

            success, output = mount_service.list_mounts()

        assert success is False
        assert "permission denied" in output

    def test_run_sudo_command_no_root(self, mount_service):
        """Test l'exécution d'une commande sudo sans être root."""
        with patch('os.geteuid', return_value=1000), \
             patch('src.services.mount_service.SudoPasswordDialog.ask_sudo_password', return_value="secret"), \
             patch('src.services.mount_service.subprocess.run') as mock_run:

            mock_run.return_value = MagicMock(returncode=0, stdout="output")

            success, output = mount_service._run_sudo_command(
                ["ls", "/root"],
                parent_window=MagicMock()
            )

            assert success is True
            assert output == "output"
            mock_run.assert_called_once()
            args, kwargs = mock_run.call_args
            assert args[0] == ["sudo", "-S", "ls", "/root"]
            assert kwargs.get("input") == "secret"

    def test_run_sudo_command_cancelled(self, mount_service):
        """Test l'annulation de la saisie du mot de passe sudo."""
        with patch('os.geteuid', return_value=1000), \
             patch('src.services.mount_service.SudoPasswordDialog.ask_sudo_password', return_value=None), \
             patch('src.services.mount_service.subprocess.run') as mock_run:

            success, output = mount_service._run_sudo_command(
                ["ls", "/root"],
                parent_window=MagicMock()
            )

            assert success is False
            assert output == "Sudo password required"
            mock_run.assert_not_called()

    def test_run_sudo_command_as_root(self, mount_service):
        """Test l'exécution d'une commande sudo en étant root."""
        with patch('os.geteuid', return_value=0), \
             patch('src.services.mount_service.subprocess.run') as mock_run:

            mock_run.return_value = MagicMock(returncode=0, stdout="root output")

            success, output = mount_service._run_sudo_command(["ls", "/root"])

            assert success is True
            assert output == "root output"
            mock_run.assert_called_once()
            assert mock_run.call_args[0][0] == ["ls", "/root"]

    def test_run_sudo_command_error(self, mount_service):
        """Test la gestion des erreurs dans _run_sudo_command."""
        with patch('os.geteuid', return_value=0), \
             patch('src.services.mount_service.subprocess.run') as mock_run:

            mock_run.side_effect = subprocess.CalledProcessError(1, "cmd", stderr="boom")

            success, output = mount_service._run_sudo_command(["invalid-command"])

            assert success is False
            assert "boom" in output

    def test_mount_with_special_characters(self, mount_service, mock_run_command, mock_credentials, mock_fs_ops):
        """Test le montage avec des caractères spéciaux dans les chemins."""
        mock_run_command.return_value = (True, "")
        mock_credentials.create_credentials_file.return_value = "/tmp/creds"

        result = mount_service.mount_share(
            server="sérvèr",
            share="p@th",
            mount_point="/mnt/point spécial",
            username="user@domain",
            password="p@ssw0rd#"
        )

        assert result[0] is True
        cmd = mock_run_command.call_args[0][0]
        assert cmd[-2] == "//sérvèr/p@th"
        assert cmd[-1] == "/mnt/point spécial"

    def test_multiple_mounts(self, mount_service, mock_run_command, mock_credentials, mock_fs_ops):
        """Test plusieurs montages successifs."""
        mock_run_command.return_value = (True, "")

        result1 = mount_service.mount_share("server", "share1", "/mnt/point1", "user", "pass")
        result2 = mount_service.mount_share("server", "share2", "/mnt/point2", "user", "pass")

        assert result1[0] is True
        assert result2[0] is True
        assert mock_run_command.call_count == 2

    def test_cleanup_credentials(self, mount_service):
        """Test le nettoyage des fichiers d'identifiants après démontage."""
        mount_service.active_credentials["/mnt/point"] = "/tmp/creds"
        with patch('os.path.exists', return_value=True), \
             patch('os.unlink') as mock_unlink:
            mount_service._cleanup_credentials("/mnt/point")

        mock_unlink.assert_called_once_with("/tmp/creds")
        assert "/mnt/point" not in mount_service.active_credentials

    def test_cleanup_credentials_missing_file(self, mount_service):
        """Test le nettoyage quand le fichier d'identifiants n'existe plus."""
        mount_service.active_credentials["/mnt/point"] = "/tmp/creds"
        with patch('os.path.exists', return_value=False), \
             patch('os.unlink') as mock_unlink:
            mount_service._cleanup_credentials("/mnt/point")

        mock_unlink.assert_not_called()
        assert "/mnt/point" not in mount_service.active_credentials
