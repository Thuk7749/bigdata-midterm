# Improved Debug Mode Design - No Global Variables

## Problems with Global Variables

The original design used a global `DEBUG_MODE` variable, which has several issues:
- **Tight coupling**: Functions depend on global state
- **Testing difficulty**: Hard to test different debug modes in the same test suite
- **Thread safety**: Global state can cause issues in multi-threaded environments
- **Code clarity**: Not obvious from function signatures what affects their behavior
- **Maintainability**: Changes to global state can have unexpected side effects

## Solution: Explicit Parameter Passing

Instead of using global variables, I've refactored the code to pass the `debug_mode` parameter explicitly through the call chain:

### Function Signatures Updated

```python
# Before (using global variable)
def print_debug_traceback():
    if DEBUG_MODE:  # Depends on global state
        ...

def execute_frequent_itemsets_finding(...) -> bool:
    # No indication that debug behavior exists
    ...

# After (explicit parameters)
def print_debug_traceback(debug_mode: bool = False):
    if debug_mode:  # Clear dependency
        ...

def execute_frequent_itemsets_finding(..., debug_mode: bool = False) -> bool:
    # Clear from signature that debug mode is supported
    ...
```

### Call Chain Flow

```
main() 
├── args.debug (from command line)
├── frequent_itemsets_mining(..., debug_mode=args.debug)
    ├── execute_frequent_itemsets_finding(..., debug_mode)
    │   ├── suppress_mrjob_output(debug_mode)
    │   └── print_debug_traceback(debug_mode)
    ├── execute_candidate_2_itemsets_generation(..., debug_mode)
    │   └── print_debug_traceback(debug_mode)
    └── execute_candidate_itemsets_generation(..., debug_mode)
        ├── suppress_mrjob_output(debug_mode)
        └── print_debug_traceback(debug_mode)
```

## Benefits of the New Design

1. **Clear Dependencies**: Each function's signature shows exactly what it needs
2. **Easy Testing**: Can test debug and non-debug modes independently
3. **Thread Safe**: No shared global state
4. **Functional Style**: Functions are pure with explicit inputs/outputs
5. **Better Documentation**: Function signatures serve as documentation
6. **Maintainable**: Changes are localized and predictable

## Alternative Approaches Considered

### Option 1: Configuration Object (Alternative)
```python
@dataclass
class AlgorithmConfig:
    min_support_count: int = 4
    runner_mode: str = "inline"
    max_iterations: int = 100
    debug_mode: bool = False
    hadoop_args: list[str] | None = None
    owner: str | None = None

def frequent_itemsets_mining(*input_paths: str, config: AlgorithmConfig) -> None:
    ...
```

### Option 2: Context Manager (Alternative)
```python
@contextlib.contextmanager
def debug_context(debug_mode: bool):
    # Set up debug context
    yield DebugHelper(debug_mode)
    # Clean up
```

### Option 3: Logger-based Approach (Alternative)
```python
import logging

# Configure logger based on debug flag
logger = logging.getLogger(__name__)
if debug_mode:
    logger.setLevel(logging.DEBUG)
```

## Why Parameter Passing is Best Here

For this use case, explicit parameter passing is the best choice because:
- **Simple**: No need for complex configuration objects
- **Clear**: Obvious what each function does
- **Lightweight**: Minimal overhead
- **Consistent**: Matches the existing code style
- **Debuggable**: Easy to trace debug behavior through the call chain

## Usage Examples

```bash
# Normal mode (clean output)
python main.py trans01 trans02 --min-support 3 --runner hadoop

# Debug mode (shows MRJob output and stack traces)
python main.py trans01 trans02 --min-support 3 --runner hadoop --debug
```

The debug flag now flows cleanly through the entire call chain without any global state dependencies.
