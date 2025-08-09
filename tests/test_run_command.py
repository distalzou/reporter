"""Tests for reporter.run_command module."""

import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path
from reporter.run_command import run_reporter_cmd


class TestRunReporterCmd:
    """Tests for run_reporter_cmd function."""
    
    @patch('reporter.run_command.run_command')
    @patch('reporter.run_command.tempfile.mkdtemp')
    @patch('reporter.run_command.Path')
    def test_run_reporter_cmd_command_construction(self, mock_path_class, mock_mkdtemp, mock_run_command):
        """Test that run_reporter_cmd constructs commands correctly."""
        # Setup mocks
        temp_dir = "/tmp/reporter_test"
        mock_mkdtemp.return_value = temp_dir
        mock_temp_path = MagicMock()
        mock_temp_path.rglob.return_value = []  # No new files
        mock_path_class.return_value = mock_temp_path
        
        mock_run_command.return_value.__enter__.return_value = (
            iter(["output line"]), "stderr", 0
        )
        
        # Call function
        cmd_args = ["Finance.getAccounts"]
        reporter_dir = "/test/reporter"
        
        with run_reporter_cmd(cmd_args, reporter_dir=reporter_dir) as (stdout, stderr, code, files):
            list(stdout)  # Consume the iterator
        
        # Verify temporary directory was created
        mock_mkdtemp.assert_called_once_with(prefix="reporter_")
        
        # Verify run_command was called with correct arguments
        expected_cmd = ["java", "-jar", "Reporter.jar", "p=Reporter.properties", "Finance.getAccounts"]
        mock_run_command.assert_called_once_with(
            cmd=expected_cmd,
            timeout=300.0,
            working_dir=mock_temp_path
        )
    
    @patch('reporter.run_command.run_command')
    @patch('reporter.run_command.tempfile.mkdtemp')
    @patch('reporter.run_command.Path')
    def test_run_reporter_cmd_multiple_args(self, mock_path_class, mock_mkdtemp, mock_run_command):
        """Test run_reporter_cmd with multiple command arguments."""
        # Setup mocks
        mock_mkdtemp.return_value = "/tmp/reporter_test"
        mock_temp_path = MagicMock()
        mock_temp_path.rglob.return_value = []
        mock_path_class.return_value = mock_temp_path
        
        mock_run_command.return_value.__enter__.return_value = (
            iter([]), "", 0
        )
        
        cmd_args = ["Sales.getReport", "Daily_Summary", "20240101"]
        
        with run_reporter_cmd(cmd_args) as (stdout, stderr, code, files):
            pass
        
        expected_cmd = [
            "java", "-jar", "Reporter.jar", "p=Reporter.properties",
            "Sales.getReport", "Daily_Summary", "20240101"
        ]
        mock_run_command.assert_called_once()
        call_args = mock_run_command.call_args[1]
        assert call_args['cmd'] == expected_cmd
        assert call_args['timeout'] == 300.0
    
    @patch('reporter.run_command.run_command')
    @patch('reporter.run_command.tempfile.mkdtemp')
    @patch('reporter.run_command.Path')
    def test_run_reporter_cmd_custom_timeout(self, mock_path_class, mock_mkdtemp, mock_run_command):
        """Test run_reporter_cmd with custom timeout."""
        # Setup mocks
        mock_mkdtemp.return_value = "/tmp/reporter_test"
        mock_temp_path = MagicMock()
        mock_temp_path.rglob.return_value = []
        mock_path_class.return_value = mock_temp_path
        
        mock_run_command.return_value.__enter__.return_value = (
            iter([]), "", 0
        )
        
        with run_reporter_cmd(["test"], timeout=600.0) as (stdout, stderr, code, files):
            pass
        
        call_args = mock_run_command.call_args[1]
        assert call_args['timeout'] == 600.0
    
    @patch('reporter.run_command.run_command')
    @patch('reporter.run_command.tempfile.mkdtemp')
    @patch('reporter.run_command.Path')
    @patch('reporter.run_command.logger')
    def test_run_reporter_cmd_exception_handling(self, mock_logger, mock_path_class, mock_mkdtemp, mock_run_command):
        """Test run_reporter_cmd exception handling and logging."""
        # Setup mocks
        mock_mkdtemp.return_value = "/tmp/reporter_test"
        mock_temp_path = MagicMock()
        mock_path_class.return_value = mock_temp_path
        mock_run_command.side_effect = Exception("Test error")
        
        with pytest.raises(Exception, match="Test error"):
            with run_reporter_cmd(["test"]):
                pass
        
        mock_logger.error.assert_called_once()
        error_call = mock_logger.error.call_args
        assert "Failed to run reporter command" in error_call[0]
        assert error_call[1]['error'] == "Test error"
        assert 'temp_dir' in error_call[1]
    
    @patch('reporter.run_command.run_command')
    @patch('reporter.run_command.tempfile.mkdtemp')
    @patch('reporter.run_command.Path')
    def test_run_reporter_cmd_file_tracking(self, mock_path_class, mock_mkdtemp, mock_run_command):
        """Test that run_reporter_cmd tracks new files created."""
        # Setup mocks
        mock_mkdtemp.return_value = "/tmp/reporter_test"
        mock_temp_path = MagicMock()
        
        # Mock files created (non-symlinks)
        mock_file1 = MagicMock()
        mock_file1.is_file.return_value = True
        mock_file1.is_symlink.return_value = False
        mock_file2 = MagicMock()
        mock_file2.is_file.return_value = True
        mock_file2.is_symlink.return_value = False
        mock_symlink = MagicMock()
        mock_symlink.is_file.return_value = True
        mock_symlink.is_symlink.return_value = True
        
        mock_temp_path.rglob.return_value = [mock_file1, mock_file2, mock_symlink]
        mock_path_class.return_value = mock_temp_path
        
        mock_run_command.return_value.__enter__.return_value = (
            iter(["output"]), "", 0
        )
        
        with run_reporter_cmd(["test"]) as (stdout, stderr, code, files):
            pass
        
        # Should return only non-symlink files
        assert files == [mock_file1, mock_file2]
    
    @patch('reporter.run_command.run_command')
    @patch('reporter.run_command.tempfile.mkdtemp')
    @patch('reporter.run_command.Path')
    def test_run_reporter_cmd_symlink_creation(self, mock_path_class, mock_mkdtemp, mock_run_command):
        """Test that run_reporter_cmd creates symlinks to Reporter files."""
        # Setup mocks
        temp_dir_path = "/tmp/reporter_test"
        reporter_dir = "/path/to/reporter"
        
        mock_mkdtemp.return_value = temp_dir_path
        mock_temp_path = MagicMock()
        mock_temp_path.rglob.return_value = []
        
        # Mock reporter directory and files
        mock_reporter_path = MagicMock()
        mock_jar_source = MagicMock()
        mock_jar_source.exists.return_value = True
        mock_jar_source.resolve.return_value = Path("/resolved/Reporter.jar")
        mock_properties_source = MagicMock()
        mock_properties_source.exists.return_value = True
        mock_properties_source.resolve.return_value = Path("/resolved/Reporter.properties")
        
        mock_reporter_path.__truediv__ = lambda self, name: mock_jar_source if name == "Reporter.jar" else mock_properties_source
        
        # Mock symlink targets
        mock_jar_symlink = MagicMock()
        mock_properties_symlink = MagicMock()
        mock_temp_path.__truediv__ = lambda self, name: mock_jar_symlink if name == "Reporter.jar" else mock_properties_symlink
        
        def path_constructor(path):
            if path == temp_dir_path:
                return mock_temp_path
            elif path == reporter_dir:
                return mock_reporter_path
            return MagicMock()
        
        mock_path_class.side_effect = path_constructor
        
        mock_run_command.return_value.__enter__.return_value = (
            iter([]), "", 0
        )
        
        with run_reporter_cmd(["test"], reporter_dir=reporter_dir) as (stdout, stderr, code, files):
            pass
        
        # Verify symlinks were created
        mock_jar_symlink.symlink_to.assert_called_once_with(Path("/resolved/Reporter.jar"))
        mock_properties_symlink.symlink_to.assert_called_once_with(Path("/resolved/Reporter.properties"))