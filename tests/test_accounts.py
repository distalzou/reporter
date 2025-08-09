"""Tests for reporter.accounts module."""

import pytest
from unittest.mock import patch, MagicMock
from reporter.accounts import Account, account_tuples


class TestAccount:
    """Tests for Account dataclass."""
    
    def test_account_creation(self):
        """Test Account dataclass creation."""
        account = Account(name="Test Account", id=12345)
        assert account.name == "Test Account"
        assert account.id == 12345
    
    def test_account_equality(self):
        """Test Account equality comparison."""
        account1 = Account(name="Test", id=123)
        account2 = Account(name="Test", id=123)
        account3 = Account(name="Other", id=123)
        
        assert account1 == account2
        assert account1 != account3


class TestAccountFunctions:
    """Tests for account-related functions."""
    
    @patch('reporter.accounts.account_lines')
    def test_account_tuples_success(self, mock_account_lines):
        """Test account_tuples with successful response."""
        # Mock successful subprocess output - format matches actual regex: "name, id"
        mock_account_lines.return_value = [
            "Test Account 1, 12345",
            "Test Account 2, 67890"
        ]
        
        accounts = list(account_tuples())
        
        assert len(accounts) == 2
        assert accounts[0] == Account(name="Test Account 1", id=12345)
        assert accounts[1] == Account(name="Test Account 2", id=67890)
    
    @patch('reporter.accounts.account_lines')
    def test_account_tuples_empty_response(self, mock_account_lines):
        """Test account_tuples with empty response."""
        mock_account_lines.return_value = []
        
        accounts = list(account_tuples())
        assert accounts == []
    
    @patch('reporter.accounts.account_lines')
    def test_account_tuples_malformed_line(self, mock_account_lines):
        """Test account_tuples with malformed input."""
        mock_account_lines.return_value = [
            "Valid Account, 12345",
            "Invalid line format",
            "Another Valid, 67890"
        ]
        
        accounts = list(account_tuples())
        
        # Should skip malformed line and continue
        assert len(accounts) == 2
        assert accounts[0] == Account(name="Valid Account", id=12345)
        assert accounts[1] == Account(name="Another Valid", id=67890)