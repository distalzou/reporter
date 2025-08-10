# Apple Reporter CLI

A Python CLI tool that automates retrieval of Apple's Reporter.jar reports. This tool wraps Apple's Reporter.jar (Java application) to fetch sales and financial reports across multiple accounts, vendors, regions, and date ranges.

## Features

- **Automated Report Fetching**: Batch download reports across date ranges
- **Multi-Account Support**: Handle multiple App Store Connect accounts
- **Comprehensive Coverage**: Fetch reports for all vendors and regions
- **Structured Logging**: Detailed logging with contextual information
- **Robust Error Handling**: Graceful handling of missing data and errors

## Prerequisites

### Required Software
- **Python 3.13+**: This project uses modern Python features
- **Java Runtime**: Required to run Apple's Reporter.jar
- **uv**: Modern Python package manager (recommended)

### Apple Reporter Setup

1. **Download Reporter.jar** from Apple:
   - Log into [App Store Connect](https://appstoreconnect.apple.com/)
   - Go to Sales and Trends � Reports
   - Download the Reporter.jar tool

2. **Create Reporter.properties** file:
   ```properties
   Sales.userID=your_userid
   Sales.password=your_app_specific_password
   Finance.userID=your_userid  
   Finance.password=your_app_specific_password
   ```
   
   **Security Note**: Use App Store Connect API keys or app-specific passwords. Never use your main Apple ID password.

3. **Directory Structure**:
   ```
   Reporter/
      Reporter.jar
      Reporter.properties
   ```

## Installation

### Using uv (recommended)
```bash
git clone <repository-url>
cd reporter
uv install
```

### Using pip
```bash
git clone <repository-url>  
cd reporter
pip install -e .
```

## Configuration

1. **Set up Reporter directory**: Place `Reporter.jar` and `Reporter.properties` in a `Reporter/` directory
2. **Update configuration**: Modify the reporter directory path in your environment or configuration

## Usage

### Basic Commands

```bash
# Show help
uv run reporter --help

# List available accounts
uv run reporter accounts

# List available report types
uv run reporter reports_available

# Fetch reports for a date range
uv run reporter batchfetch --start 2024-01 --end 2024-12

# Alternative syntax with individual date components
uv run reporter batchfetch --start_year 2024 --start_month 1 --end_year 2024 --end_month 12
```

### Batch Fetching Examples

```bash
# Fetch reports for the entire year 2024
uv run reporter batchfetch --start 2024-01 --end 2024-12

# Fetch reports for Q1 2024
uv run reporter batchfetch --start 2024-01 --end 2024-03

# Fetch reports for a single month
uv run reporter batchfetch --start 2024-06 --end 2024-06
```

## Output

Downloaded reports are saved as compressed text files in the Reporter directory with the naming pattern:
```
{vendor_id}_{MMYY}_{region}.txt.gz
```

Example: `80051061_0124_US.txt.gz`

## Development

### Setup Development Environment
```bash
uv install --dev
```

### Code Quality Tools
```bash
# Lint code
uv run ruff check

# Format code  
uv run ruff format

# Type check
uv run mypy src/

# Run tests
uv run pytest
```

### Project Structure

```
src/
   reporter/           # Main package
      cmd.py         # CLI interface using Typer
      batchfetch.py  # Bulk report fetching logic
      run_command.py # Subprocess management for Reporter.jar
      accounts.py    # Account discovery and management
      reports_available.py # Report type discovery
   asynclib/          # Reusable async utilities
      async_subprocess_manager.py
```

## How It Works

1. **Account Discovery**: Queries Reporter.jar for available App Store Connect accounts
2. **Report Discovery**: Identifies available report types for each account  
3. **Batch Processing**: Iterates through accounts � vendors � regions � date periods
4. **Report Fetching**: Calls Reporter.jar with specific parameters for each report
5. **File Management**: Downloads and compresses reports with structured naming

## Error Handling

The tool handles various scenarios gracefully:

- **No Data Available**: Reporter.jar returns exit code 1 when no sales data exists for a date
- **Authentication Issues**: Clear error messages for credential problems
- **Network Issues**: Timeout handling and retry logic
- **File System**: Proper cleanup of temporary directories

## Logging

The tool uses structured logging to provide detailed information:

```bash
# Set log level (default: INFO)
export REPORTER_LOG_LEVEL=DEBUG
```

Log messages include contextual information such as:
- Account and vendor details
- Date ranges being processed
- File paths and operations
- Error details and troubleshooting info

## Troubleshooting

### Common Issues

**"No sales for date specified"**
- This is normal for periods with no app sales or downloads
- The tool logs this as informational, not an error

**Authentication failures**
- Verify Reporter.properties credentials
- Ensure you're using app-specific passwords, not your main Apple ID password
- Check that your account has access to the requested data

**Java not found**
- Install Java runtime environment
- Verify `java` is available in your PATH: `java -version`

**Permission denied errors**
- Check file permissions on Reporter.jar and Reporter.properties
- Ensure the Reporter directory is writable for output files

### Getting Help

1. Check the logs for detailed error information
2. Verify your Reporter.jar setup with Apple's documentation
3. Test with a small date range first
4. Open an issue with logs and configuration details

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass: `uv run pytest`
6. Run code quality checks: `uv run ruff check && uv run mypy src/`
7. Submit a pull request

## Disclaimer

This tool is not affiliated with Apple Inc. Reporter.jar is Apple's official reporting tool - this project simply provides a Python wrapper for automation purposes. Use in accordance with Apple's terms of service.