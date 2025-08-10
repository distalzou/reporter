"""Interface to apple's Reporter.jar"""

import re
import logging
import structlog
from typing import Annotated
import reporter.batchfetch
import reporter.accounts
import reporter.reports_available
import typer

def parse_date_string(date_str: str) -> tuple[int, int]:
    """Parse YYYY-MM date string into year and month integers.
    
    Args:
        date_str: Date string in YYYY-MM format
        
    Returns:
        Tuple of (year, month)
        
    Raises:
        ValueError: If date string format is invalid
    """
    if not re.match(r'^\d{4}-\d{2}$', date_str):
        raise ValueError(f"Date must be in YYYY-MM format, got: {date_str}")
    
    year_str, month_str = date_str.split('-')
    year, month = int(year_str), int(month_str)
    
    if not 1 <= month <= 12:
        raise ValueError(f"Month must be 1-12, got: {month}")
    
    return year, month

app = typer.Typer(add_completion=False, help="Automation for Apple's Reporter.jar")

@app.command("batchfetch", help="Fetch all reports available, for all known accounts and all vendors in each account, in the given date range, using either individual date components or date strings.")
def batchfetch(
    start_year:  Annotated[int | None, typer.Option("--start_year")] = None,
    start_month: Annotated[int | None, typer.Option("--start_month")] = None,
    end_year:    Annotated[int | None, typer.Option("--end_year")] = None,
    end_month:   Annotated[int | None, typer.Option("--end_month")] = None,
    start:       Annotated[str | None, typer.Option("--start", help="date string YYYY-MM")] = None,
    end:         Annotated[str | None, typer.Option("--end",   help="date string YYYY-MM")] = None,
) -> None:
    """Process data within a date range.
    
    Use either:
    - Individual date components: --start_year 2024 --start_month 1 --end_year 2024 --end_month 12
    - Date strings:               --start 2024-01                   --end 2024-12
    """
    # Check for conflicting arguments
    individual_args  = [start_year, start_month, end_year, end_month]
    date_string_args = [start, end]
    
    individual_provided  = any(arg is not None for arg in individual_args)
    date_string_provided = any(arg is not None for arg in date_string_args)
    
    if individual_provided and date_string_provided:
        raise typer.BadParameter("Cannot mix individual date arguments with date string arguments")   
    if not individual_provided and not date_string_provided:
        raise typer.BadParameter("Must provide either individual date arguments or date strings")
    
    # Parse arguments based on format
    if date_string_provided:
        if start is None or end is None:
            raise typer.BadParameter("Both --start and --end must be provided when using date strings")
        
        try:
            start_year, start_month = parse_date_string(start)
            end_year,   end_month   = parse_date_string(end)
        except ValueError as e:
            raise typer.BadParameter(str(e))
    
    else:  # individual_provided
        if start_year is None or start_month is None or end_year is None or end_month is None:
            raise typer.BadParameter("All individual date arguments must be provided: --start_year, --start_month, --end_year, --end_month")
        
        # Validate month ranges
        if not 1 <= start_month <= 12:
            raise typer.BadParameter(f"start_month must be 1-12, got: {start_month}")
        if not 1 <= end_month <= 12:
            raise typer.BadParameter(f"end_month must be 1-12, got: {end_month}")
    
    # Call the actual processing function
    reporter.batchfetch.batch_fetch(start_year, start_month, end_year, end_month)

@app.command("accounts", help="List accounts")
def accounts() -> None:
    reporter.accounts.accounts()

@app.command("reports_available", help="List available reports")
def reports_available() -> None:
    reporter.reports_available.reports_available()

def main() -> None:
    """Entry point for the CLI."""
    # show logging messages at this level and above
    logging.basicConfig(level=logging.INFO)
    # Configure structlog to use the standard library logger
    structlog.configure(
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
    )
    app()


if __name__ == "__main__":
    main()