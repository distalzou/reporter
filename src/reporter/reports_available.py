import re
from dataclasses import dataclass
from reporter.run_command import run_reporter_cmd
from reporter.accounts import account_tuples
import structlog
from collections import defaultdict
from typing import Iterator

logger = structlog.get_logger(__name__)

@dataclass
class AvailableReport:
    vendor:      int
    region:      str
    report_type: str

def reports_available() -> None:
    """List available reports for all accounts."""
    print("Collecting report data for all accounts...")

    data = dict()
    for account in account_tuples():
        print(f"Account: {account.name}, ID: {account.id}")
        account_data: defaultdict[int, defaultdict[str, list[str]]] = defaultdict(lambda: defaultdict(list))
        for report in reports_available_tuples(account.id):
            account_data[report.vendor][report.report_type].append(report.region)
        data[account.id] = account_data

    for account_id, reports in data.items():
        print(f"Account ID: {account_id}")
        for vendor, report_types in reports.items():
            print(f"  Vendor: {vendor}")
            for report_type, regions in report_types.items():
                print(f"    Report Type: {report_type}")
                print(f"    Regions: {','.join(regions)}")
    logger.info("Finished listing available reports.")

def reports_available_lines(account_id: int) -> Iterator:
    """List available reports per vendor."""
    with run_reporter_cmd([f"a={account_id}", "Finance.getVendorsAndRegions"], reporter_dir="/Users/devin/src/reporter/Reporter") as (stdout_lines, stderr_text, exit_code, new_files):
        # Warn about unexpected file creation during reports listing
        if new_files:
            logger.warning("Unexpected files created during reports listing", 
                          account_id=account_id, files=[str(f) for f in new_files])
        
        if exit_code == 0:
            for line in stdout_lines:
                yield line.strip()
        else:
            stdout_text = ''.join(stdout_lines)
            output = f"stdout: '{stdout_text}' " if stdout_text else ''
            output += f"stderr: '{stderr_text}' " if stderr_text else ''
            logger.warning(f"Failed to fetch reports and vendors: exit code {exit_code} {output}")

def reports_available_tuples(account_id: int) -> Iterator[AvailableReport]:
    """Yield AvailableReport objects for each report available for each vendor."""
    for line in reports_available_lines(account_id):
        if line:
            # The following reports are available for vendor 85797441
            match = re.match(r'.+vendor (\d+)', line)
            if match:
                vendor = int(match.group(1))
                continue
            region, report_types = line.split(":")
            if region and report_types:
                for report_type in report_types.split(", "):
                    yield AvailableReport(vendor=vendor, region=region, report_type=report_type)
            else:
                logger.warning(f"Failed to parse line: {line}")

