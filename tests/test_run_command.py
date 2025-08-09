"""Tests for reporter.run_command module."""

import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path
from reporter.run_command import run_reporter_cmd


class TestRunReporterCmd:
    """Tests for run_reporter_cmd function."""
    
    @patch('reporter.run_command.run_command')
    def test_run_reporter_cmd_command_construction(self, mock_run_command):
        """Test that run_reporter_cmd constructs commands correctly."""
        # Setup mock
        mock_run_command.return_value.__enter__.return_value = (
            iter(["output line"]), "stderr", 0
        )
        
        # Call function
        cmd_args = ["Finance.getAccounts"]
        working_dir = "/test/dir"
        
        with run_reporter_cmd(cmd_args, working_dir=working_dir) as (stdout, stderr, code):
            list(stdout)  # Consume the iterator
        
        # Verify run_command was called with correct arguments
        expected_cmd = ["java", "-jar", "Reporter.jar", "p=Reporter.properties", "Finance.getAccounts"]
        mock_run_command.assert_called_once_with(
            cmd=expected_cmd,
            timeout=300.0,
            working_dir=working_dir
        )
    
    @patch('reporter.run_command.run_command')
    def test_run_reporter_cmd_multiple_args(self, mock_run_command):
        """Test run_reporter_cmd with multiple command arguments."""
        mock_run_command.return_value.__enter__.return_value = (
            iter([]), "", 0
        )
        
        cmd_args = ["Sales.getReport", "Daily_Summary", "20240101"]
        
        with run_reporter_cmd(cmd_args):
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
    def test_run_reporter_cmd_custom_timeout(self, mock_run_command):
        """Test run_reporter_cmd with custom timeout."""
        mock_run_command.return_value.__enter__.return_value = (
            iter([]), "", 0
        )
        
        with run_reporter_cmd(["test"], timeout=600.0):
            pass
        
        call_args = mock_run_command.call_args[1]
        assert call_args['timeout'] == 600.0
    
    @patch('reporter.run_command.run_command')
    @patch('reporter.run_command.logger')
    def test_run_reporter_cmd_exception_handling(self, mock_logger, mock_run_command):
        """Test run_reporter_cmd exception handling and logging."""
        mock_run_command.side_effect = Exception("Test error")
        
        with pytest.raises(Exception, match="Test error"):
            with run_reporter_cmd(["test"]):
                pass
        
        mock_logger.error.assert_called_once_with(
            "Failed to run reporter command", 
            error="Test error"
        )