# Contributing Guidelines

## Welcome

This repository is part of a personal learning journey. While contributions aren't actively sought, feedback and discussions are always welcome!

## Reporting Issues

If you find a bug or have suggestions for improvement, please submit an issue with detailed information.

## Code Standards

- Follow PEP 8 for Python code.
- Use `black` for formatting.
- Run `flake8` for linting.

## Testing

### Test Structure

- Tests use pytest and are located in the `./tests` directory
- Test data files are stored in `./tests/data`
- Test file names should follow the pattern `test_*.py`

### Test Data Generation

The project includes a test mbox generator for creating standardized test data:

```bash
python ./tests/data/generate_test_mbox.py --count [16|32]
```

This creates reproducible test files with various email formats, headers, content types, and attachments.

### Running Tests

To run the test suite:

```bash
pytest
```

To run specific tests:

```bash
pytest ./tests/test_mbox_generator.py
```

## Pull Requests

- Fork the repository and create a new branch for your changes.
- Submit a pull request with a clear description of what your changes address.
- Ensure all tests pass before submitting your PR.

## Contact

Feel free to reach out if you'd like to discuss this project or share feedback!
