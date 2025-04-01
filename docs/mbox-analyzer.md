mbox_analyzer.txt
for: mbox_analyzer.py

Basic Usage:

	python mbox_analyzer.py path/to/file.mbox

With optional arguments:

	python mbox_analyzer.py path/to/file.mbox --output report.json --visualize --summary

The script provides:

1. Detailed analysis of .mbox files including:
	- File metadata (size, email count)
	- Header analysis (From, To, CC, BCC, Subject, Date)
	- Body and attachment analysis
	- Content size comparison
	- Statistical summary

2. Output options:
	- Console output (default)
	- JSON report file (with --output option) ie report.json
	- Markdown report summary (with --summary (or -s) flag) report.md (Only works with --output flag, not stdout)
	- Visualizations (with --visualize option)
		- Top senders chart
		- Email distribution by month
		- Attachment types pie chart
		- Body size comparison

3. Error handling and logging:
	- Comprehensive error reporting
	- Progress logging during analysis
	- Warning for non-.mbox files

Requirements:
	- The script requires Python 3 and uses the following standard libraries:
		- mailbox, email for .mbox processing
		- json for report generation
		- os, sys for file operations
		- logging for status messages
		- collections for data analysis
		- matplotlib (optional) for visualisations

Exit codes:
	0: Success
	1: File not found
	2: Analysis failed

The report will be generated in JSON format, either written to the specified output file or printed to stdout if no output file is specified.