"""Simple test suite for utils modules - avoiding pytest I/O capture issues."""

import os
import sys


def test_colors_exist():
    """Test that Colors class can be imported."""
    from utils.cli import Colors
    assert hasattr(Colors, 'RED')
    assert hasattr(Colors, 'BOLD')


def test_cli_exists():
    """Test that CLI class can be imported."""
    from utils.cli import CLI
    cli = CLI(no_color=True)
    assert cli is not None


def test_cli_generators_dict():
    """Test CLI has generators dictionary."""
    from utils.cli import CLI
    cli = CLI(no_color=True)
    assert isinstance(cli.GENERATORS, dict)
    assert len(cli.GENERATORS) > 0


def test_banner_module():
    """Test banner module can be imported."""
    from utils import banner
    assert hasattr(banner, 'print_banner')


def test_menu_module():
    """Test menu module can be imported."""
    from utils import menu
    assert menu is not None


def test_utils_structure():
    """Test utils directory structure."""
    utils_path = os.path.join(os.path.dirname(__file__), '..', 'utils')
    assert os.path.isdir(utils_path)
    assert os.path.isfile(os.path.join(utils_path, '__init__.py'))
    assert os.path.isfile(os.path.join(utils_path, 'cli.py'))
    assert os.path.isfile(os.path.join(utils_path, 'banner.py'))
    assert os.path.isfile(os.path.join(utils_path, 'menu.py'))
