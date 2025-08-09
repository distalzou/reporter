import re
from datetime import date
from dateutil.relativedelta import relativedelta
from typing import Iterator
from reporter.run_command import run_reporter_cmd
from reporter.accounts import account_tuples, Account
from reporter.reports_available import reports_available_tuples, AvailableReport
import structlog
logger = structlog.get_logger(__name__)

# A simple stepped date range generator, yields each period in the range
def date_range(start: date, end: date, delta: relativedelta) -> Iterator[date]:
    current = start
    while current <= end:
        yield current
        current += delta

def batch_fetch(
    start_year: int,
    start_month: int,
    end_year: int,
    end_month: int,
) -> None:
    """Fetch reports for the given date range.
    
    Args:
        start_year: Starting year
        start_month: Starting month (1-12)
        end_year: Ending year
        end_month: Ending month (1-12)
    """    
    start = date(start_year, start_month, 1)
    end   = date(end_year,   end_month,   1)

    if start > end:
        raise ValueError("Start date must be before end date")
    
    for period in date_range(start, end, relativedelta(months=1)):
        print(f"Fetching reports for {period.strftime('%Y-%m')}...")
        fetch_all_reports_for_period(period.year, period.month)

def fetch_all_reports_for_period(year: int, month: int) -> None:
    for account in account_tuples():
        print(f"Fetching reports for account: {account.name} (ID: {account.id})")
        for report in reports_available_tuples(account.id):
            get_report(report, account, year, month)

def get_report(report: AvailableReport, account: Account, year: int, month: int) -> None:
    # Finance.getReport: Downloads a report
    cmd_args = [f"a={account.id}",
                "Finance.getReport",
                f"{report.vendor},",        # Vendor Number
                f"{report.region},",        # Region Code
                f"{report.report_type},",   # Report Type
                f"{year},",                 # Fiscal Year  
                f"{month},"]                # Fiscal Period
    with run_reporter_cmd(
        cmd_args=cmd_args,
        working_dir="/Users/devin/src/reporter/Reporter"
    ) as (stdout_lines, stderr_text, exit_code):
        stdout_text = ''.join(stdout_lines)
        desc = f"{report.vendor} in {report.region} for {year}-{month:02d}"
        if exit_code == 0:
            match = re.match(r'Successfully downloaded (.+)', stdout_text.rstrip())
            if match:
                filename = match.group(1)
                logger.info(f"{desc}: Downloaded report {filename}")
            else:
                logger.warning(f"{desc}: Unexpected output: {stdout_text.rstrip()}")
        else:
            if exit_code == 1:
                if stdout_text.rstrip() == "There were no sales for the date specified.":
                    logger.info(f"{desc}: No sales data available")
                else:
                    logger.warning(f"{desc}: Failed to fetch report {report.report_type}: {stdout_text.rstrip()}")
            else:
                output = f"stdout: '{stdout_text}' " if stdout_text else ''
                output += f"stderr: '{stderr_text}' " if stderr_text else ''
                logger.warning(f"{desc}: Failed to fetch report {report.report_type}: exit code {exit_code} {output}")
