import subprocess
from contextlib import contextmanager, chdir
from typing import Optional, Union, Iterator, Generator
from collections.abc import Sequence
import io
import signal
from pathlib import Path
import structlog

logger = structlog.get_logger(__name__)

@contextmanager
def run_reporter_cmd(
    cmd_args: list[str],
    timeout: float = 300.0,
    working_dir: Optional[Union[str, Path]] = None
) -> Iterator[tuple[Iterator[str], str, int]]:
    command = ["java", "-jar", "Reporter.jar", "p=Reporter.properties"] + cmd_args
    try:
        with run_command(
            cmd=command,
            timeout=timeout, 
            working_dir=working_dir
        ) as (stdout_lines, stderr_text, exit_code):
            yield stdout_lines, stderr_text, exit_code
    except Exception as e:
        logger.error("Failed to run reporter command", error=str(e))
        raise

@contextmanager
def run_command(
    cmd: Sequence[str], 
    timeout: Optional[float] = None,
    kill_on_timeout: bool = True,
    working_dir: Path | str = '.'
) -> Iterator[tuple[Generator[str, None, None], str, int]]:
    """
    Run a command and return stdout as an iterable, stderr as string, and exit code.
    
    Handles process cleanup, timeouts, and signals gracefully.
    NOTE: Does not return anything until the command completes and all output is read and buffered.
    
    Args:
        cmd: Command and arguments to execute
        timeout: Maximum time to wait for command completion (seconds)
        kill_on_timeout: If True, kill process on timeout; if False, terminate gracefully
        
    Yields:
        Tuple of (stdout_lines_iterator, stderr_text, exit_code)
        
    Raises:
        subprocess.TimeoutExpired: If timeout is exceeded
        
    Example:
        with run_command(['ls', '-la'], timeout=30.0) as (stdout_lines, stderr_text, exit_code):
            for line in stdout_lines:
                print(line.rstrip())
            print(f"Errors: {stderr_text}")
            print(f"Exit code: {exit_code}")
    """
    logger.debug("Starting subprocess", command=cmd, cwd=working_dir)
    with chdir(working_dir):
        with subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,  
            text=True,
            bufsize=1
        ) as proc:
            try:
                # Read output with optional timeout
                communicate_kwargs = dict()
                if timeout is not None:
                    communicate_kwargs['timeout'] = timeout
                stdout_text, stderr_text = proc.communicate(**communicate_kwargs)
                    
            except subprocess.TimeoutExpired:
                # Handle timeout - clean up process
                if kill_on_timeout:
                    proc.kill()  # SIGKILL - forceful
                else:
                    proc.terminate()  # SIGTERM - graceful
                
                # Still try to get partial output
                try:
                    stdout_text, stderr_text = proc.communicate(timeout=5.0)
                except subprocess.TimeoutExpired:
                    # Process really won't die, force kill
                    proc.kill()
                    stdout_text, stderr_text = proc.communicate()
                
                # Re-raise the timeout exception
                raise
                
            except KeyboardInterrupt:
                # Handle Ctrl+C gracefully
                proc.terminate()
                try:
                    proc.communicate(timeout=2.0)
                except subprocess.TimeoutExpired:
                    proc.kill()
                    proc.communicate()
                raise
            
            # Process completed normally or was cleaned up
            # proc.returncode is now available
            exit_code = proc.returncode
            
            # Handle signal-based exits (negative return codes on Unix)
            if exit_code < 0:
                # Process was killed by signal
                signal_num  = -exit_code
                signal_name = signal.Signals(signal_num).name if hasattr(signal, 'Signals') else f"SIG{signal_num}"
                stderr_text += f"\nProcess killed by signal {signal_num} ({signal_name})\n"
            
            yield (io.StringIO(stdout_text), stderr_text, exit_code)


# Example usage
if __name__ == "__main__":
    # Basic usage
    with run_command(['ls', '-la']) as (stdout_lines, stderr_text, exit_code):
        for line in stdout_lines:
            print(f"OUT: {line.rstrip()}")
        print(f"ERR: {stderr_text}")
        print(f"EXIT: {exit_code}")
    
    # With timeout
    try:
        with run_command(['sleep', '10'], timeout=2.0) as (stdout_lines, stderr_text, exit_code):
            print("This won't be reached")
    except subprocess.TimeoutExpired:
        print("Command timed out!")
    
    # Handle command that exits with error
    with run_command(['ls', '/nonexistent']) as (stdout_lines, stderr_text, exit_code):
        print(f"Exit code: {exit_code}")  # Will be non-zero
        if stderr_text:
            print(f"Error: {stderr_text}")

@contextmanager
def run_command_v1(cmd: Sequence[str]) -> Iterator[tuple[Generator[str, None, None], str, int]]:
    """
    Run a command and return stdout as an iterable, stderr as string, and exit code.
    
    Note: This reads all output into memory first to avoid deadlocks with large outputs
    that exceed pipe buffer sizes.
    
    Args:
        cmd: Command and arguments to execute
        
    Yields:
        Tuple of (stdout_lines_iterator, stderr_text, exit_code)
        
    Example:
        with run_command(['ls', '-la']) as (stdout_lines, stderr_text, exit_code):
            for line in stdout_lines:
                print(line.rstrip())
            print(f"Errors: {stderr_text}")
            print(f"Exit code: {exit_code}")
    """
    with subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,  
        text=True,
        bufsize=1
    ) as proc:
        # Pre-fetch both stdout and stderr to avoid deadlock
        # This prevents hanging if output exceeds pipe buffer size
        stdout_text = proc.stdout.read() if proc.stdout else ""
        stderr_text = proc.stderr.read() if proc.stderr else ""
        
        # Wait for process to complete to get exit code
        proc.wait()
        
        # Yield stdout as line generator, stderr text, exit code
        yield (io.StringIO(stdout_text), stderr_text, proc.returncode)


# Example usage
if __name__ == "__main__":
    with run_command(['ls', '-la']) as (stdout_lines, stderr_text, exit_code):
        for line in stdout_lines:
            print(f"OUT: {line.rstrip()}")
        print(f"ERR: {stderr_text}")
        print(f"EXIT: {exit_code}")