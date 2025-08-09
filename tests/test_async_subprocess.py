"""Tests for asynclib.async_subprocess_manager module."""

from asynclib.async_subprocess_manager import SubprocessError


class TestSubprocessError:
    """Tests for SubprocessError exception class."""
    
    def test_subprocess_error_creation(self):
        """Test SubprocessError creation with message only."""
        error = SubprocessError("Test error message")
        assert str(error) == "Test error message"
        assert error.return_code is None
    
    def test_subprocess_error_with_return_code(self):
        """Test SubprocessError creation with return code."""
        error = SubprocessError("Process failed", return_code=1)
        assert str(error) == "Process failed"
        assert error.return_code == 1
    
    def test_subprocess_error_inheritance(self):
        """Test SubprocessError inherits from Exception."""
        error = SubprocessError("Test")
        assert isinstance(error, Exception)
        
        # Can be caught as regular Exception
        try:
            raise error
        except Exception as e:
            assert isinstance(e, SubprocessError)
            assert str(e) == "Test"