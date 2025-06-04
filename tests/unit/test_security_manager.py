import os
import pytest

from config.app_config import AppConfig
from utils.security_manager import IntegratedSecurityManager
from utils.error_handler import SecurityError


def test_get_encryption_key_requires_env(tmp_path):
    """get_encryption_key should raise SecurityError when env var is missing"""
    # Backup current environment variable
    original = os.environ.pop('COMPENSATION_SYSTEM_ENCRYPTION_KEY', None)
    try:
        config = AppConfig()
        config.database_directory = str(tmp_path)
        security_manager = IntegratedSecurityManager(config)
        with pytest.raises(SecurityError):
            security_manager.get_encryption_key()
    finally:
        if original is not None:
            os.environ['COMPENSATION_SYSTEM_ENCRYPTION_KEY'] = original
