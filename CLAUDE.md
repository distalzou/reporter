# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Python CLI tool that automates retrieval of Apple's Reporter.jar reports. The tool wraps Apple's Reporter.jar (Java application) to fetch sales/financial reports across multiple accounts, vendors, regions, and date ranges.

## Development Commands

### Package Management
- Install dependencies: `uv install`
- Install with dev dependencies: `uv install --dev`
- Add new dependency: `uv add <package>`
- Add dev dependency: `uv add --dev <package>`

### Code Quality
- Lint code: `uv run ruff check`
- Format code: `uv run ruff format`  
- Type check: `uv run mypy src/`
- Run tests: `uv run pytest`

### Application Commands
- Run CLI: `uv run reporter --help`
- List accounts: `uv run reporter accounts`
- List available reports: `uv run reporter reports_available`
- Batch fetch reports: `uv run reporter batchfetch --start 2024-01 --end 2024-12`

## Architecture

### Core Components
- **reporter.cmd**: CLI interface using Typer, main entry point
- **reporter.batchfetch**: Orchestrates bulk report fetching across date ranges
- **reporter.run_command**: Subprocess management for Java Reporter.jar execution
- **reporter.accounts**: Account discovery and management
- **reporter.reports_available**: Report type discovery
- **asynclib.async_subprocess_manager**: Async alternative for subprocess handling

### Key Dependencies
- **Reporter.jar**: External Java application (Apple's reporting tool) located in `/Reporter/` directory
- **Reporter.properties**: Configuration file for Reporter.jar authentication
- Compressed report files in `/Reporter/` directory with naming pattern: `{vendor_id}_{MMYY}_{region}.txt.gz`

### Data Flow
1. CLI commands parse date ranges and options
2. Account discovery queries Reporter.jar for available accounts
3. Report discovery queries available report types per account
4. Batch processing iterates through accounts × vendors × regions × date periods
5. Each report fetch calls Reporter.jar with specific parameters
6. Downloaded reports are saved as compressed text files

### Subprocess Handling
The codebase includes two approaches for subprocess management:
- **Synchronous**: `run_command.py` with context managers and timeout handling  
- **Asynchronous**: `async_subprocess_manager.py` with graceful cancellation

Both handle:
- Process cleanup and signal handling
- Timeout management
- Error reporting and logging

### File Organization
- `src/reporter/`: Main package with CLI and business logic
- `src/asynclib/`: Reusable async utilities
- `Reporter/`: Contains Apple's Reporter.jar and downloaded report files
- Output files follow pattern: `{account_id}_{MMDD}_{region_code}.txt.gz`

### Error Handling
- Reporter.jar exit codes: 0 = success, 1 = no data available, other = error
- Structured logging with contextual information for troubleshooting
- Graceful handling of missing data periods ("no sales for date specified")

## Git Commit Guidelines

- Keep commit messages concise and descriptive
- Do not include Claude Code attribution or "Generated with Claude" text in commit messages
- Focus commit messages on what changed and why