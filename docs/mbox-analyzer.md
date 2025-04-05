# MBOX Analyzer Documentation

## Overview

The MBOX Analyzer is a Python script that processes and analyzes .mbox files, generating comprehensive reports about their contents.

## Basic Usage

From project root:

```bash
python ./src/mbox_analyzer.py path/to/file.mbox
```

With optional arguments:
```bash
python ./src/mbox_analyzer.py path/to/file.mbox --output report.json --visualize --summary
```

## Features

### 1. Detailed Analysis
The script analyzes .mbox files and provides:
- File metadata (size, email count)
- Header analysis (From, To, CC, BCC, Subject, Date)
- Body and attachment analysis
- Content size comparison
- Statistical summary

### 2. Output Options
- Console output (default)
- JSON report file (with `--output` option) ie `report.json`
- Markdown report summary (with `--summary` or `-s` flag)
  - Note: Only works with `--output` flag, not stdout
- Visualizations (with `--visualize` option)
  - Top senders chart
  - Email distribution by month
  - Attachment types pie chart
  - Body size comparison

### 3. Error Handling and Logging
- Comprehensive error reporting
- Progress logging during analysis
- Warning for non-.mbox files

## Requirements

The script requires Python 3 and uses the following standard libraries:
- `mailbox`, `email` - for .mbox processing
- `json` - for report generation
- `os`, `sys` - for file operations
- `logging` - for status messages
- `collections` - for data analysis
- `matplotlib` (optional) - for visualizations

## Exit Codes
| Code | Description |
|------|-------------|
| 0    | Success |
| 1    | File not found |
| 2    | Analysis failed |

## Output Format
The report will be generated in JSON format, either written to the specified output file or printed to stdout if no output file is specified.

## Test Data Generation

The project includes a test data generator that creates .mbox files with various email formats, headers, content types, and attachments for testing purposes.

### Usage

From the project root:

```bash
python ./tests/data/generate_test_mbox.py --count [16|32] [--output OUTPUT_PATH]
```

If no output path is specified, the file will be created as `./tests/data/sample{count}.mbox`.

### Features

The test data generator produces emails with:

1. **Header Variations**
   - From/To with display names
   - CC and BCC fields
   - Various date formats
   - Message-ID variations
   - Reply-To headers
   - Auto-reply headers
   - Encoded headers with non-ASCII characters

2. **Content Type Variations**
   - Plain text emails
   - HTML-only emails
   - Mixed content (text/html) emails

3. **Charset Variations**
   - UTF-8 encoding
   - ASCII encoding
   - ISO-8859-1 encoding

4. **Attachment Variations**
   - Text file attachments
   - PDF file attachments (simulated)
   - Image file attachments (simulated)
   - Multiple attachments in a single email

### Examples

Generate a standard test file with 16 emails:
```bash
python ./tests/data/generate_test_mbox.py
```

Generate a larger test file with 32 emails:
```bash
python ./tests/data/generate_test_mbox.py --count 32
```

Generate a test file in a custom location:
```bash
python ./tests/data/generate_test_mbox.py --output ./custom/path/test.mbox
```

### Integration with Testing

The generated test files can be used with the analyzer:

```bash
python ./src/mbox_analyzer.py ./tests/data/sample16.mbox
```

This enables comprehensive testing of all analyzer features against a variety of email formats and edge cases.
