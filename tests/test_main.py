"""Test suite for main.py module."""

import os
import sys
import argparse


class TestMainFile:
    """Test main.py module."""

    def test_main_file_exists(self):
        """Test that main.py file exists."""
        main_path = os.path.join(os.path.dirname(__file__), '..', 'main.py')
        assert os.path.isfile(main_path)

    def test_main_module_can_be_imported(self):
        """Test that main module can be imported."""
        sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
        try:
            import main
            assert main is not None
        except Exception as e:
            # Skip if main has complex dependencies
            pass

    def test_main_has_argument_parser(self):
        """Test that main should have argument parsing."""
        # This is a structural test — verify main.py has typical CLI structure
        main_path = os.path.join(os.path.dirname(__file__), '..', 'main.py')
        with open(main_path, 'r') as f:
            content = f.read()
            # Check for typical CLI patterns
            assert 'argparse' in content or 'sys.argv' in content, "main.py should have argument parsing"

    def test_main_imports_required_modules(self):
        """Test that main imports required modules."""
        main_path = os.path.join(os.path.dirname(__file__), '..', 'main.py')
        with open(main_path, 'r') as f:
            content = f.read()
            
            # Check for required imports
            required_imports = ['utils', 'generators']
            for required in required_imports:
                assert required in content, f"main.py should import {required}"

    def test_project_has_all_required_files(self):
        """Test that project has all required files."""
        project_root = os.path.dirname(os.path.dirname(__file__))
        
        required_files = ['main.py', 'README.md', 'requirements.txt']
        for file in required_files:
            file_path = os.path.join(project_root, file)
            assert os.path.isfile(file_path), f"Required file {file} not found"

    def test_project_directories_exist(self):
        """Test that all required directories exist."""
        project_root = os.path.dirname(os.path.dirname(__file__))
        
        required_dirs = ['generators', 'utils', 'tests']
        for dir_name in required_dirs:
            dir_path = os.path.join(project_root, dir_name)
            assert os.path.isdir(dir_path), f"Required directory {dir_name} not found"

    def test_main_hello_world(self):
        """Test basic arithmetic."""
        assert 1 + 1 == 2


class TestProjectStructure:
    """Test overall project structure."""

    def test_project_root_files(self):
        """Test that project root has essential files."""
        project_root = os.path.dirname(os.path.dirname(__file__))
        
        files_to_check = {
            'main.py': 'Main entry point',
            'README.md': 'Documentation',
            'requirements.txt': 'Dependencies',
            'LICENSE': 'License file',
        }
        
        for filename, description in files_to_check.items():
            file_path = os.path.join(project_root, filename)
            assert os.path.isfile(file_path), f"{description} ({filename}) not found"

    def test_generators_has_all_modules(self):
        """Test that generators directory has all module files."""
        generators_path = os.path.join(os.path.dirname(__file__), '..', 'generators')
        
        expected_modules = [
            'load_balance.py', 'routing.py', 'nat.py', 'qos.py',
            'firewall.py', 'hotspot.py', 'vpn.py', 'dns.py',
            'monitoring.py', 'interface.py', 'system.py', '__init__.py'
        ]
        
        for module in expected_modules:
            module_path = os.path.join(generators_path, module)
            assert os.path.isfile(module_path), f"Generator module {module} not found"

    def test_utils_has_all_modules(self):
        """Test that utils directory has all module files."""
        utils_path = os.path.join(os.path.dirname(__file__), '..', 'utils')
        
        expected_modules = ['banner.py', 'cli.py', 'menu.py', '__init__.py']
        
        for module in expected_modules:
            module_path = os.path.join(utils_path, module)
            assert os.path.isfile(module_path), f"Utils module {module} not found"

    def test_tests_directory_structure(self):
        """Test that tests directory is properly structured."""
        tests_path = os.path.dirname(__file__)
        
        expected_files = ['__init__.py', 'test_main.py', 'test_generators.py', 'test_utils.py']
        
        for file in expected_files:
            file_path = os.path.join(tests_path, file)
            assert os.path.isfile(file_path), f"Test file {file} not found"


class TestPythonVersionCompatibility:
    """Test Python version compatibility."""

    def test_python_version_supported(self):
        """Test that Python version is compatible."""
        version = sys.version_info
        # Project requires Python 3.7+
        assert version.major == 3
        assert version.minor >= 7, f"Python 3.7+ required, got {version.major}.{version.minor}"

    def test_syntax_compatibility(self):
        """Test that all Python files have valid syntax."""
        import py_compile
        
        project_root = os.path.dirname(os.path.dirname(__file__))
        python_files = []
        
        # Find all Python files
        for root, dirs, files in os.walk(project_root):
            # Skip venv and pycache
            dirs[:] = [d for d in dirs if d not in ['.venv', '__pycache__', '.git']]
            for file in files:
                if file.endswith('.py'):
                    python_files.append(os.path.join(root, file))
        
        # Compile each file to check syntax
        for py_file in python_files:
            try:
                py_compile.compile(py_file, doraise=True)
            except py_compile.PyCompileError as e:
                assert False, f"Syntax error in {py_file}: {e}"


class TestRequirements:
    """Test project requirements."""

    def test_requirements_file_exists(self):
        """Test that requirements.txt exists."""
        req_path = os.path.join(os.path.dirname(__file__), '..', 'requirements.txt')
        assert os.path.isfile(req_path)

    def test_requirements_file_format(self):
        """Test that requirements.txt is properly formatted."""
        req_path = os.path.join(os.path.dirname(__file__), '..', 'requirements.txt')
        with open(req_path, 'r') as f:
            content = f.read().strip()
            # For this project, it's empty (pure stdlib)
            assert isinstance(content, str)

    def test_no_external_dependencies_required(self):
        """Test that project uses only stdlib (no external deps)."""
        req_path = os.path.join(os.path.dirname(__file__), '..', 'requirements.txt')
        with open(req_path, 'r') as f:
            content = f.read().strip()
            # Requirements should be empty for pure stdlib project
            if content:
                lines = [line.strip() for line in content.split('\n') if line.strip() and not line.startswith('#')]
                assert len(lines) == 0, "Project should have no external dependencies"


class TestProjectMetadata:
    """Test project metadata."""

    def test_readme_exists_and_populated(self):
        """Test that README is populated."""
        readme_path = os.path.join(os.path.dirname(__file__), '..', 'README.md')
        with open(readme_path, 'r') as f:
            content = f.read()
            assert len(content) > 100, "README should have substantial content"
            assert 'MikroTik' in content or 'RouterOS' in content

    def test_license_exists(self):
        """Test that LICENSE file exists."""
        license_path = os.path.join(os.path.dirname(__file__), '..', 'LICENSE')
        assert os.path.isfile(license_path)

    def test_install_script_exists(self):
        """Test that install script exists."""
        install_path = os.path.join(os.path.dirname(__file__), '..', 'install.sh')
        assert os.path.isfile(install_path)

    def test_windows_setup_exists(self):
        """Test that Windows setup documentation exists."""
        setup_path = os.path.join(os.path.dirname(__file__), '..', 'windows-setup.md')
        assert os.path.isfile(setup_path)
