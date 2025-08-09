import re
from dataclasses import dataclass
from reporter.run_command import run_reporter_cmd
import structlog
from typing import Iterator

logger = structlog.get_logger(__name__)

@dataclass
class Account:
    name: str
    id: int

def accounts() -> None:
    """List accounts."""
    print("Listing accounts...")
    for account in account_tuples():
        print(f"Account: {account.name}, ID: {account.id}")
    logger.info("Finished listing accounts.")

def account_lines() -> Iterator:
    """List accounts."""
    with run_reporter_cmd(["Finance.getAccounts"], reporter_dir="/Users/devin/src/reporter/Reporter") as (stdout_lines, stderr_text, exit_code, new_files):
        # Warn about unexpected file creation during account listing
        if new_files:
            logger.warning("Unexpected files created during account listing", 
                          files=[str(f) for f in new_files])
        
        if exit_code == 0:
            for line in stdout_lines:
                yield line.strip()
        else:
            stdout_text = ''.join(stdout_lines)
            output = f"stdout: '{stdout_text}' " if stdout_text else ''
            output += f"stderr: '{stderr_text}' " if stderr_text else ''
            logger.warning(f"Failed to fetch account lines: exit code {exit_code} {output}")

def account_tuples() -> Iterator[Account]:
    """Yield account tuples asynchronously."""
    for line in account_lines():
        if line:
            match = re.match(r'(.+), (\d+)', line)
            if match:
                yield Account(name=match.group(1), id=int(match.group(2)))
            else:
                logger.warning(f"Failed to parse line: {line}")
