# EME Utils Unit Tests

This directory contains unit tests for the EME utilities module. The tests verify the core logic of the EME operations without requiring an actual Ab Initio environment.

## Running the Tests

To run the tests, you'll need Python 3.x installed. The tests use the `unittest` framework and `unittest.mock` for mocking the `air` command outputs.

### Running All Tests

```bash
python3 -m unittest discover
```

### Running a Specific Test File

```bash
python3 test_eme_utils.py
```

### Running with Verbose Output

```bash
python3 -m unittest discover -v
```

## Test Coverage

The tests cover the following functionality:

1. **Tag Object Parsing**
   - Parsing of `air tag` command output
   - Handling of different object types (graphs, DMLs, transforms)

2. **Object Operations**
   - Checking object existence
   - Exporting objects
   - Importing objects

3. **Tag Operations**
   - Checking tag existence
   - Getting tag objects
   - Exporting tags
   - Creating tags

4. **Error Handling**
   - Failed commands
   - Invalid inputs
   - Missing objects/tags

## Adding New Tests

When adding new tests:

1. Create a new test file or add to an existing one
2. Use the `@patch` decorator to mock the `air` command
3. Test both success and failure cases
4. Include docstrings explaining the test purpose

Example:
```python
@patch('eme_utils.run_air_command')
def test_new_functionality(self, mock_run_command):
    """Test description."""
    mock_run_command.return_value = (0, "success", "")
    # Test code here
``` 