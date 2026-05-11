"""Simple test suite for main module and project structure."""

import os
import sys
import py_compile


def test_main_file_exists():
    """Test that main.py file exists."""
    main_path = os.path.join(os.path.dirname(__file__), '..', 'main.py')
    assert os.path.isfile(main_path)


def test_main_syntax_valid():
    """Test that main.py has valid syntax."""
    main_path = os.path.join(os.path.dirname(__file__), '..', 'main.py')
    try:
        py_compile.compile(main_path, doraise=True)
    except py_compile.PyCompileError as e:
        assert False, f"Syntax error in main.py: {e}"


def test_main_has_imports():
    """Test that main.py has required imports."""
    main_path = os.path.join(os.path.dirname(__file__), '..', 'main.py')
    with open(main_path, 'r', encoding='utf-8') as f:
        content = f.read()
        assert 'utils' in content or 'generators' in content


def test_project_structure():
    """Test complete project structure."""
    project_root = os.path.dirname(os.path.dirname(__file__))
    
    # Check directories
    assert os.path.isdir(os.path.join(project_root, 'generators'))
    assert os.path.isdir(os.path.join(project_root, 'utils'))
    assert os.path.isdir(os.path.join(project_root, 'tests'))
    
    # Check key files
    assert os.path.isfile(os.path.join(project_root, 'main.py'))
    assert os.path.isfile(os.path.join(project_root, 'README.md'))
    assert os.path.isfile(os.path.join(project_root, 'requirements.txt'))
    assert os.path.isfile(os.path.join(project_root, 'LICENSE'))


def test_python_version_compatible():
    """Test Python version is 3.7+."""
    version = sys.version_info
    assert version.major == 3 and version.minor >= 7


def test_requirements_file():
    """Test requirements.txt file."""
    req_path = os.path.join(os.path.dirname(__file__), '..', 'requirements.txt')
    assert os.path.isfile(req_path)
    with open(req_path, 'r') as f:
        content = f.read().strip()
        # Project uses pure stdlib, so requirements should be empty or minimal
        assert isinstance(content, str)


def test_readme_exists():
    """Test README.md exists and has content."""
    readme_path = os.path.join(os.path.dirname(__file__), '..', 'README.md')
    assert os.path.isfile(readme_path)
    with open(readme_path, 'r', encoding='utf-8') as f:
        content = f.read()
        assert len(content) > 100


def test_all_generators_exist():
    """Test that all generator modules exist."""
    generators_path = os.path.join(os.path.dirname(__file__), '..', 'generators')
    expected = [
        'dns.py', 'firewall.py', 'hotspot.py', 'interface.py',
        'load_balance.py', 'monitoring.py', 'nat.py', 'qos.py',
        'routing.py', 'system.py', 'vpn.py', '__init__.py'
    ]
    for file in expected:
        assert os.path.isfile(os.path.join(generators_path, file)), f"Missing {file}"


def test_all_utils_exist():
    """Test that all utils modules exist."""
    utils_path = os.path.join(os.path.dirname(__file__), '..', 'utils')
    expected = ['banner.py', 'cli.py', 'menu.py', '__init__.py']
    for file in expected:
        assert os.path.isfile(os.path.join(utils_path, file)), f"Missing {file}"
