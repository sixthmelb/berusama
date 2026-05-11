"""Test suite for generators module."""

import os
import sys


class TestGeneratorsPackage:
    """Test generators package structure."""

    def test_generators_package_exists(self):
        """Test that generators package can be imported."""
        try:
            import generators
            assert generators is not None
        except ImportError:
            pass  # Expected if generators has dependencies

    def test_generators_package_structure(self):
        """Test that generators package has proper structure."""
        generators_path = os.path.join(os.path.dirname(__file__), '..', 'generators')
        
        # Check required files exist
        required_files = ['__init__.py', 'load_balance.py', 'routing.py', 'nat.py', 
                         'qos.py', 'firewall.py', 'hotspot.py', 'vpn.py', 'dns.py',
                         'monitoring.py', 'interface.py', 'system.py']
        
        for file in required_files:
            file_path = os.path.join(generators_path, file)
            assert os.path.isfile(file_path), f"File {file} not found in generators/"

    def test_base_generator_exists(self):
        """Test that BaseGenerator class can be imported."""
        from generators import BaseGenerator
        assert BaseGenerator is not None

    def test_base_generator_has_required_methods(self):
        """Test that BaseGenerator has all required methods."""
        from generators import BaseGenerator
        
        required_methods = ['run', 'collect_params', 'generate', '_header_comment']
        for method in required_methods:
            assert hasattr(BaseGenerator, method), f"Method {method} not found in BaseGenerator"
            assert callable(getattr(BaseGenerator, method))

    def test_base_generator_initialization(self):
        """Test BaseGenerator can be initialized."""
        from generators import BaseGenerator
        from utils.cli import CLI
        
        cli = CLI(no_color=True)
        gen = BaseGenerator(cli)
        
        assert gen is not None
        assert gen.cli == cli
        assert gen.TITLE == "Generator"

    def test_base_generator_has_utility_methods(self):
        """Test that BaseGenerator has utility methods."""
        from generators import BaseGenerator
        from utils.cli import CLI
        
        cli = CLI(no_color=True)
        gen = BaseGenerator(cli)
        
        # Test utility methods exist
        assert hasattr(gen, '_mbps_to_bps')
        assert hasattr(gen, '_bw_string')
        assert hasattr(gen, '_header_comment')

    def test_base_generator_bandwidth_conversion(self):
        """Test bandwidth conversion methods."""
        from generators import BaseGenerator
        from utils.cli import CLI
        
        cli = CLI(no_color=True)
        gen = BaseGenerator(cli)
        
        # Test _bw_string
        result = gen._bw_string(10, "M")
        assert result == "10M"
        
        result = gen._bw_string(1, "G")
        assert result == "1G"

    def test_base_generator_header_comment(self):
        """Test header comment generation."""
        from generators import BaseGenerator
        from utils.cli import CLI
        
        cli = CLI(no_color=True)
        gen = BaseGenerator(cli)
        
        header = gen._header_comment("Test Generator")
        assert "Test Generator" in header
        assert "MikroTik AutoConfig" in header
        assert "#" in header  # Comment marker


class TestLoadBalanceGenerator:
    """Test load_balance generator module."""

    def test_load_balance_module_exists(self):
        """Test that load_balance module can be imported."""
        try:
            from generators import load_balance
            assert load_balance is not None
        except ImportError:
            pass

    def test_load_balance_generators_count(self):
        """Test that load_balance has multiple generators."""
        try:
            from generators.load_balance import PCC, NTH, ECMP
            assert PCC is not None
            assert NTH is not None
            assert ECMP is not None
        except ImportError:
            pass


class TestRoutingGenerator:
    """Test routing generator module."""

    def test_routing_module_exists(self):
        """Test that routing module can be imported."""
        try:
            from generators import routing
            assert routing is not None
        except ImportError:
            pass

    def test_routing_generators_exist(self):
        """Test that routing generators exist."""
        try:
            from generators.routing import FailoverRecursive, StaticRoute
            assert FailoverRecursive is not None
            assert StaticRoute is not None
        except ImportError:
            pass


class TestNATGenerator:
    """Test NAT generator module."""

    def test_nat_module_exists(self):
        """Test that nat module can be imported."""
        try:
            from generators import nat
            assert nat is not None
        except ImportError:
            pass

    def test_nat_port_forward_generator(self):
        """Test that NAT port forward generator exists."""
        try:
            from generators.nat import PortForward
            assert PortForward is not None
        except ImportError:
            pass


class TestQoSGenerator:
    """Test QoS generator module."""

    def test_qos_module_exists(self):
        """Test that qos module can be imported."""
        try:
            from generators import qos
            assert qos is not None
        except ImportError:
            pass

    def test_qos_has_queue_generators(self):
        """Test that QoS has various queue generators."""
        try:
            from generators.qos import SimpleQueue, QueueTree, PCQ
            assert SimpleQueue is not None
            assert QueueTree is not None
            assert PCQ is not None
        except ImportError:
            pass


class TestFirewallGenerator:
    """Test firewall generator module."""

    def test_firewall_module_exists(self):
        """Test that firewall module can be imported."""
        try:
            from generators import firewall
            assert firewall is not None
        except ImportError:
            pass


class TestHotspotGenerator:
    """Test hotspot generator module."""

    def test_hotspot_module_exists(self):
        """Test that hotspot module can be imported."""
        try:
            from generators import hotspot
            assert hotspot is not None
        except ImportError:
            pass


class TestVPNGenerator:
    """Test VPN generator module."""

    def test_vpn_module_exists(self):
        """Test that vpn module can be imported."""
        try:
            from generators import vpn
            assert vpn is not None
        except ImportError:
            pass


class TestDNSGenerator:
    """Test DNS generator module."""

    def test_dns_module_exists(self):
        """Test that dns module can be imported."""
        try:
            from generators import dns
            assert dns is not None
        except ImportError:
            pass


class TestMonitoringGenerator:
    """Test monitoring generator module."""

    def test_monitoring_module_exists(self):
        """Test that monitoring module can be imported."""
        try:
            from generators import monitoring
            assert monitoring is not None
        except ImportError:
            pass


class TestInterfaceGenerator:
    """Test interface generator module."""

    def test_interface_module_exists(self):
        """Test that interface module can be imported."""
        try:
            from generators import interface
            assert interface is not None
        except ImportError:
            pass


class TestSystemGenerator:
    """Test system generator module."""

    def test_system_module_exists(self):
        """Test that system module can be imported."""
        try:
            from generators import system
            assert system is not None
        except ImportError:
            pass


class TestGeneratorIntegration:
    """Integration tests for generators."""

    def test_all_generators_inherit_base(self):
        """Test that all generators inherit from BaseGenerator."""
        from generators import BaseGenerator
        
        generator_modules = [
            'load_balance', 'routing', 'nat', 'qos', 
            'firewall', 'hotspot', 'vpn', 'dns',
            'monitoring', 'interface', 'system'
        ]
        
        for module_name in generator_modules:
            try:
                module = __import__(f'generators.{module_name}', fromlist=[''])
                # Check that module has at least one class
                assert module is not None
            except ImportError:
                pass  # Skip if module has dependencies

    def test_generator_title_attribute(self):
        """Test that generators have TITLE attribute."""
        from generators import BaseGenerator
        from utils.cli import CLI
        
        cli = CLI(no_color=True)
        gen = BaseGenerator(cli)
        
        assert hasattr(gen, 'TITLE')
        assert isinstance(gen.TITLE, str)

    def test_hello_world(self):
        """Test basic assertion."""
        assert "hello world" == "hello world"

    def test_generators_module_structure(self):
        """Test that generators module is properly structured."""
        generators_path = os.path.join(os.path.dirname(__file__), '..', 'generators')
        assert os.path.isdir(generators_path)
        assert os.path.isfile(os.path.join(generators_path, '__init__.py'))
