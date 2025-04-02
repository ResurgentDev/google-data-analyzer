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