# Debug Improvements Summary

## Problem Fixed
The Apriori algorithm was not showing stack traces when errors occurred, making debugging very difficult. The comprehensive exception handling was catching all errors but only displaying the error message without context.

## Solutions Implemented

### 1. Added Debug Mode Support
- **New import**: `import traceback` for stack trace printing
- **Global flag**: `DEBUG_MODE = False` to control debug behavior
- **Helper function**: `print_debug_traceback()` to conditionally print stack traces
- **Command line option**: `--debug` flag to enable debug mode

### 2. Enhanced Exception Handling
Updated all wrapper functions to include debug stack traces:
- `execute_frequent_itemsets_finding()`
- `execute_candidate_2_itemsets_generation()`
- `execute_candidate_itemsets_generation()`

### 3. Fixed Level 2+ Processing Issue
**Root Cause**: For levels 2+, the algorithm was incorrectly passing only the candidate file as input instead of the transaction files.

**Fix**: Modified `_step_execute_frequent_itemsets_phase()` to always pass transaction files as input. The candidate file is passed separately via the `ITEMSET_FILES_ARG_NAME` parameter.

```python
# Before (incorrect):
input_for_level = input_paths if current_level == 1 else (ci_file_path(current_level),)

# After (correct):
input_for_level = input_paths  # Always use transaction files
```

## Usage Examples

### Normal Mode (Clean Output)
```bash
python main.py trans01 trans02 --min-support 3 --runner hadoop
```

### Debug Mode (With Stack Traces)
```bash
python main.py trans01 trans02 --min-support 3 --runner hadoop --debug
```

## Benefits
1. **Easier Debugging**: Full stack traces when `--debug` is used
2. **Clean Production Output**: No clutter in normal mode
3. **Fixed Algorithm**: Level 2+ itemsets now process correctly
4. **Better Error Context**: Can see exactly where errors occur in the code

## Icon Constants Applied
Consistent visual hierarchy with these indicators:
- `🔍` TASK_INDICATOR: Operation headlines
- `🔧` SUBTASK_INDICATOR: Sub-operations  
- `✅` COMPLETION_INDICATOR: Success messages
- `❌` STOP_INDICATOR: Errors and termination
- `📊` STATS_INDICATOR: Statistics and ranges
- `📄` FILE_INDICATOR: File information
- `⚠️` WARNING_INDICATOR: Warnings and partial failures
- `🚀` START_INDICATOR: Algorithm start
- `📋` PARAM_INDICATOR: Parameters
- `🔝` TOP_INDICATOR: Top results

This comprehensive refactoring makes the codebase much more maintainable and debuggable while preserving clean user experience in normal operation.
