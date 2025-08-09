"""
Async subprocess manager with graceful cancellation handling.

Provides an async iterator interface for subprocess output with proper
cleanup on cancellation or interruption.
"""

import asyncio
import signal
import sys
from contextlib import asynccontextmanager
from pathlib import Path
from types import TracebackType
from typing import AsyncIterator, Optional, Union

import structlog

logger = structlog.get_logger(__name__)

class SubprocessError(Exception):
    """Raised when subprocess operations fail."""
    
    def __init__(self, message: str, return_code: Optional[int] = None) -> None:
        super().__init__(message)
        self.return_code = return_code


class AsyncSubprocessManager:
    """
    Manages async subprocesses with graceful cancellation handling.
    
    Provides an async iterator interface for reading subprocess output
    line by line, with proper cleanup on cancellation.
    
    Example:
        async with AsyncSubprocessManager() as manager:
            async for line in manager.run_command(["java", "-version"]):
                print(f"Output: {line}")
    """
    
    def __init__(
        self, 
        timeout: float = 30.0,
        encoding: str = "utf-8",
        working_dir: Optional[Union[str, Path]] = None
    ) -> None:
        """
        Initialize the subprocess manager.
        
        Args:
            timeout: Maximum time to wait for process completion
            encoding: Text encoding for subprocess output
            working_dir: Working directory for subprocess execution
        """
        self.timeout = timeout
        self.encoding = encoding
        self.working_dir = Path(working_dir) if working_dir else None
        self._process: Optional[asyncio.subprocess.Process] = None
        self._cleanup_done = False
        
    async def __aenter__(self) -> "AsyncSubprocessManager":
        """Async context manager entry."""
        return self
        
    async def __aexit__(
        self,
        exc_type: Optional[type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Optional[TracebackType]
    ) -> None:
        """Async context manager exit with cleanup."""
        await self._cleanup()
        
    async def run_command(
        self, 
        command: list[str],
        include_stderr: bool = True,
        working_dir: Optional[Union[str, Path]] = None
    ) -> AsyncIterator[str]:
        """
        Run a command and yield output lines asynchronously.
        
        Args:
            command: Command and arguments to execute
            include_stderr: Whether to include stderr in output stream
            
        Yields:
            Lines of output from the subprocess
            
        Raises:
            SubprocessError: If subprocess fails to start or exits with error
            asyncio.CancelledError: If the operation is cancelled
        """
        if self._process is not None:
            raise SubprocessError("Another process is already running")
            
        logger.info("Starting subprocess", command=command, cwd=working_dir or self.working_dir)
        
        try:
            # Configure stderr handling
            stderr_target = asyncio.subprocess.STDOUT if include_stderr else asyncio.subprocess.PIPE
            
            # Start the subprocess
            self._process = await asyncio.create_subprocess_exec(
                *command,
                stdout=asyncio.subprocess.PIPE,
                stderr=stderr_target,
                cwd=self.working_dir,
                text=False
            )
            
            logger.debug("Subprocess started", pid=self._process.pid)
            
            # Read output line by line
            assert self._process.stdout is not None
            async for line in self._iter_lines(self._process.stdout):
                yield line.rstrip('\n\r')
                
        except asyncio.CancelledError:
            logger.warning("Subprocess operation cancelled")
            await self._cleanup()
            raise
        except Exception as e:
            logger.error("Subprocess execution failed", error=str(e))
            await self._cleanup()
            raise SubprocessError(f"Failed to execute command: {e}") from e
        finally:
            await self._ensure_process_completion()
            
    async def _iter_lines(self, stream: asyncio.StreamReader) -> AsyncIterator[str]:
        """
        Async iterator for reading lines from a stream.
        
        Args:
            stream: The asyncio stream to read from
            
        Yields:
            Lines from the stream
        """
        try:
            while True:
                line = await asyncio.wait_for(stream.readline(), timeout=self.timeout)
                if not line:  # EOF
                    break
                yield line.decode(self.encoding) if isinstance(line, bytes) else line
        except asyncio.TimeoutError:
            logger.warning("Stream read timeout")
            raise SubprocessError(f"Stream read timeout after {self.timeout}s")
        except asyncio.CancelledError:
            logger.info("Stream reading cancelled")
            raise
            
    async def _cleanup(self) -> None:
        """Clean up the subprocess gracefully."""
        if self._cleanup_done or self._process is None:
            return
            
        self._cleanup_done = True
        logger.info("Cleaning up subprocess", pid=self._process.pid)
        
        try:
            # Try graceful termination first
            if self._process.returncode is None:
                self._process.terminate()
                try:
                    await asyncio.wait_for(self._process.wait(), timeout=5.0)
                    logger.info("Subprocess terminated gracefully")
                except asyncio.TimeoutError:
                    logger.warning("Graceful termination failed, killing process")
                    # Force kill if graceful termination fails
                    self._process.kill()
                    await self._process.wait()
                    logger.info("Subprocess killed")
                    
        except ProcessLookupError:
            # Process already terminated
            logger.info("Subprocess already terminated")
        except Exception as e:
            logger.error("Error during cleanup", error=str(e))
            
    async def _ensure_process_completion(self) -> None:
        """Ensure the process has completed and check return code."""
        if self._process is None:
            return
            
        try:
            return_code = await self._process.wait()
            logger.debug("Subprocess completed", return_code=return_code)
            
            if return_code != 0:
                error_msg = f"Process exited with code {return_code}"
                # Try to read any remaining stderr
                if self._process.stderr and not self._process.stderr.at_eof():
                    try:
                        stderr_data = await asyncio.wait_for(
                            self._process.stderr.read(), 
                            timeout=1.0
                        )
                        if stderr_data:
                            error_output = stderr_data.decode(self.encoding).strip()
                            error_msg += f"\nError output: {error_output}"
                    except (asyncio.TimeoutError, UnicodeDecodeError):
                        pass
                        
                raise SubprocessError(error_msg, return_code)
                
        except asyncio.CancelledError:
            raise
        finally:
            self._process = None


@asynccontextmanager
async def run_java_command(
    java_args: list[str], 
    timeout: float = 30.0,
    working_dir: Optional[Union[str, Path]] = None
) -> AsyncIterator[AsyncIterator[str]]:
    """
    Convenience context manager for running Java commands.
    
    Args:
        java_args: Java command arguments (without 'java' prefix)
        timeout: Command timeout in seconds
        working_dir: Working directory for command execution
        
    Yields:
        Async iterator of output lines
        
    Example:
        async with run_java_command(["-version"]) as output:
            async for line in output:
                print(f"Java output: {line}")
    """
    command = ["java"] + java_args

    async with AsyncSubprocessManager(
        timeout=timeout, 
        working_dir=working_dir
    ) as manager:
        yield manager.run_command(command)

@asynccontextmanager
async def run_reporter_cmd(
    cmd_args: list[str],
    timeout: float = 300.0,
    working_dir: Optional[Union[str, Path]] = None
) -> AsyncIterator[AsyncIterator[str]]:
    command = ["java", "-jar", "Reporter.jar", "p=Reporter.properties"] + cmd_args
    try:
        async with AsyncSubprocessManager(
            timeout=timeout, 
            working_dir=working_dir
        ) as manager:
            yield manager.run_command(command)
    except SubprocessError as e:
        logger.error("Failed to run reporter command", error=str(e))

def setup_signal_handlers() -> None:
    """Set up signal handlers for graceful shutdown."""
    def signal_handler(signum: int, frame) -> None:
        logger.info("Received signal, shutting down", signal=signum)
        # Get the current event loop and create a task to cancel all running tasks
        try:
            loop = asyncio.get_running_loop()
            for task in asyncio.all_tasks(loop):
                if not task.done():
                    task.cancel()
        except RuntimeError:
            # No running event loop
            pass
        
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)


# Example usage and testing
async def example_usage() -> None:
    """Example of how to use the AsyncSubprocessManager."""
    setup_signal_handlers()
    
    try:
        # Example 1: Direct manager usage
        async with AsyncSubprocessManager(timeout=10.0) as manager:
            print("Running 'java -version':")
            async for line in manager.run_command(["java", "-version"]):
                print(f"  {line}")
                
        print("\n" + "="*50 + "\n")
        
        # Example 2: Convenience function
        async with run_java_command(["-cp", ".", "MyClass"]) as output:
            print("Running Java class:")
            async for line in output:
                print(f"  {line}")
                
    except SubprocessError as e:
        print(f"Subprocess error: {e}")
        if e.return_code:
            print(f"Return code: {e.return_code}")
    except asyncio.CancelledError:
        print("Operation was cancelled")
    except KeyboardInterrupt:
        print("\nInterrupted by user")


if __name__ == "__main__":
    # Configure structured logging
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.dev.ConsoleRenderer()
        ],
        wrapper_class=structlog.make_filtering_bound_logger(20),  # INFO level
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )
    
    try:
        asyncio.run(example_usage())
    except KeyboardInterrupt:
        print("\nShutdown complete")
        sys.exit(0)