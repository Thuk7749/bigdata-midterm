"""
Main driver for the Apriori algorithm implementation using MapReduce.

This module orchestrates the complete Apriori frequent itemset mining process
by coordinating candidate generation and support counting phases through
multiple MapReduce jobs until no new frequent itemsets are found.

Algorithm Flow:
1. Level 1: Count individual items using ItemsetSupportCounter
2. Level 2: Generate 2-itemset candidates using combinatorial approach
3. Level 3+: Use CandidateGenerator + ItemsetSupportCounter pipeline
4. Repeat until no new frequent itemsets found or max iterations reached

Key Functions:
- frequent_itemsets_mining(): Main algorithm orchestrator
- Logging and output formatting utilities
- Command-line argument parsing and validation
"""
import os
import argparse
import time
import sys
import contextlib
import traceback

from collections.abc import Callable
from io import StringIO

# Import core functions and constants from apriori_core
from apriori_core import (
    find_frequent_itemsets,
    generate_candidate_2_itemsets,
    generate_candidate_itemsets,
    combine_parts,
    extract_itemsets_and_supports,
    is_empty_file,
    _refresh_directory,
    # Constants
    FREQUENT_ITEMSETS_FILE_NAME_PREFIX,
    CANDIDATE_ITEMSETS_FILE_NAME_PREFIX,
    FILE_NAME_SEPARATOR,
    FILE_EXTENSION,
    FREQUENT_ITEMSETS_DIR,
    CANDIDATE_ITEMSETS_DIR,
    PARTS_SUBDIR
)

# Constants for argument names
MIN_SUPPORT_CMD_ARG = "--min-support"
RUNNER_CMD_ARG = "--runner"
MAX_ITERATIONS_CMD_ARG = "--max-iterations"
CLEAN_CMD_ARG = "--clean"
HADOOP_ARGS_CMD_ARG = "--hadoop-args"
OWNER_CMD_ARG = "--owner"
DEBUG_CMD_ARG = "--debug"

# Default values for command-line arguments
DEFAULT_MIN_SUPPORT = 4
DEFAULT_RUNNER_MODE = "inline"
DEFAULT_MAX_ITERATIONS = 100

# Icon constants for consistent visual hierarchy
TASK_INDICATOR = "-" * 100 +  "\n🛠️ "     # Operation headlines (Finding, Generating)
FILE_INDICATOR = "📄 "         # File information
SUBTASK_INDICATOR = "🔧 "      # Sub-operations (Combining parts)
COMPLETION_INDICATOR = "✅ "   # Found, Generated, Combined messages
WARNING_INDICATOR = "⚠️ "      # Warnings and partial failures
STOP_INDICATOR = "❌ "         # No conditions and termination
STATS_INDICATOR = "📊 "        # Statistics and support ranges

# Core operation wrapper functions
# -------------------------------------------------------------------------------------------------

# pylint: disable=broad-exception-caught,too-many-arguments,too-many-positional-arguments
def execute_frequent_itemsets_finding(
    input_paths: tuple[str, ...],
    level: int,
    min_support_count: int,
    runner_mode: str,
    hadoop_args: list[str] | None = None,
    owner: str | None = None,
    debug_mode: bool = False,
) -> bool:
    """
    Execute frequent itemset finding with comprehensive error handling.

    Args:
        input_paths: Transaction file paths for processing
        level: Current itemset size level
        min_support_count: Minimum support threshold
        runner_mode: MapReduce execution mode
        hadoop_args: Additional Hadoop arguments
        owner: Owner for Hadoop jobs
        debug_mode: Enable detailed error reporting

    Returns:
        bool: True if successful, False if error occurred
    """
    try:
        with suppress_mrjob_output(debug_mode):
            find_frequent_itemsets(
                *input_paths,
                level=level,
                min_support_count=min_support_count,
                runner_mode=runner_mode,
                hadoop_args=hadoop_args,
                owner=owner,
            )
        return True
    except ValueError as e:
        print(f"{STOP_INDICATOR} Configuration error in frequent itemset finding: {e}")
        print_debug_traceback(debug_mode)
        return False
    except (RuntimeError, OSError, IOError) as e:
        print(f"{STOP_INDICATOR} MapReduce job failed for frequent itemsets: {e}")
        print_debug_traceback(debug_mode)
        return False
    except Exception as e:
        print(f"{STOP_INDICATOR} Unexpected error in frequent itemsets: {e}")
        print_debug_traceback(debug_mode)
        return False
# pylint: enable=broad-exception-caught,too-many-arguments,too-many-positional-arguments

# pylint: disable=broad-exception-caught
def execute_candidate_2_itemsets_generation(
    frequent_itemsets_file: str,
    debug_mode: bool = False,
) -> tuple[bool, int]:
    """
    Execute 2-itemset candidate generation with error handling and result display.

    Args:
        frequent_itemsets_file: Path to frequent 1-itemsets file
        debug_mode: Enable detailed error reporting

    Returns:
        tuple: (success: bool, candidates_generated: int)
    """
    try:
        candidates_generated = generate_candidate_2_itemsets(frequent_itemsets_file)
        return True, candidates_generated
    except (FileNotFoundError, IOError) as e:
        print(f"{STOP_INDICATOR} File access error in 2-itemset generation: {e}")
        print_debug_traceback(debug_mode)
        return False, 0
    except ValueError as e:
        print(f"{STOP_INDICATOR} Data validation error in 2-itemset generation: {e}")
        print_debug_traceback(debug_mode)
        return False, 0
    except Exception as e:  # pragma: no cover
        print(f"{STOP_INDICATOR} Unexpected error in 2-itemset generation: {e}")
        print_debug_traceback(debug_mode)
        return False, 0
# pylint: enable=broad-exception-caught

# pylint: disable=broad-exception-caught,too-many-arguments,too-many-positional-arguments
def execute_candidate_itemsets_generation(
    frequent_itemsets_file: str,
    level: int,
    runner_mode: str,
    hadoop_args: list[str] | None = None,
    owner: str | None = None,
    debug_mode: bool = False,
) -> bool:
    """
    Execute candidate itemsets generation for levels 3+ with error handling.

    Args:
        frequent_itemsets_file: Path to frequent itemsets file from previous level
        level: Target itemset size level
        runner_mode: MapReduce execution mode
        hadoop_args: Additional Hadoop arguments
        owner: Owner for Hadoop jobs
        debug_mode: Enable detailed error reporting

    Returns:
        bool: True if successful, False if error occurred
    """
    try:
        with suppress_mrjob_output(debug_mode):
            generate_candidate_itemsets(
                frequent_itemsets_file,
                level=level,
                runner_mode=runner_mode,
                hadoop_args=hadoop_args,
                owner=owner,
            )
        return True
    except ValueError as e:
        print(f"{STOP_INDICATOR} Configuration error in candidate generation: {e}")
        print_debug_traceback(debug_mode)
        return False
    except (RuntimeError, OSError, IOError) as e:
        print(f"{STOP_INDICATOR} MapReduce job failed for candidate generation: {e}")
        print_debug_traceback(debug_mode)
        return False
    except Exception as e:  # pragma: no cover
        print(f"{STOP_INDICATOR} Unexpected error in candidate generation: {e}")
        print_debug_traceback(debug_mode)
        return False
# pylint: enable=broad-exception-caught,too-many-arguments,too-many-positional-arguments

def frequent_itemsets_mining(
    *input_paths: str,
    min_support_count: int = 4,
    runner_mode: str = "inline",
    max_iterations: int = 100,
    hadoop_args: list[str] | None = None,
    owner: str | None = None,
    debug_mode: bool = False,
) -> None:
    """
    Execute the complete Apriori algorithm for frequent itemset mining.

    Orchestrates the iterative process of finding frequent itemsets and
    generating candidates until no new frequent itemsets are discovered
    or maximum iterations are reached.

    Args:
        *input_paths (str): Paths to transaction files for processing.
        min_support_count (int): Minimum support threshold (default: 4).
        runner_mode (str): MapReduce execution mode (default: "inline").
        max_iterations (int): Maximum algorithm iterations (default: 100).
        hadoop_args (list[str], optional): Additional Hadoop arguments to pass to MRJob.
        owner (str, optional): Owner for Hadoop jobs when using hadoop runner.
        debug_mode (bool): Enable detailed error reporting and MRJob output.
    """
    # File path helper functions
    fi_file_path: Callable[[int], str] = lambda level: (
        os.path.join(
            FREQUENT_ITEMSETS_DIR,
            f"{FREQUENT_ITEMSETS_FILE_NAME_PREFIX}{FILE_NAME_SEPARATOR}{level}{FILE_EXTENSION}"
        )
    )
    ci_file_path: Callable[[int], str] = lambda level: (
        os.path.join(
            CANDIDATE_ITEMSETS_DIR,
            f"{CANDIDATE_ITEMSETS_FILE_NAME_PREFIX}{FILE_NAME_SEPARATOR}{level}{FILE_EXTENSION}"
        )
    )

    # Algorithm state
    current_level: int = 1
    current_iteration: int = 0
    total_frequent_itemsets = 0

    # Step 1: Initialize algorithm and log start
    def _step_initialize_algorithm() -> float:
        """Initialize algorithm logging and input file validation."""
        algorithm_start = log_operation_start(
            "Apriori Algorithm",
            min_support=min_support_count,
            runner_mode=runner_mode,
            max_iterations=max_iterations,
            input_files=list(input_paths)
        )

        return algorithm_start

    # Step 2: Log current operation and inputs
    def _step_log_iteration_inputs() -> None:
        """Log the current operation and input files."""
        if current_level == 1:
            print(f"\n{TASK_INDICATOR} Finding frequent 1-itemsets (individual items)")
            for i, path in enumerate(input_paths, 1):
                log_file_info(path, f"Input transaction file {i}")
        else:
            print(f"\n{TASK_INDICATOR} Finding frequent {current_level}-itemsets")
            candidate_file_path = ci_file_path(current_level)
            log_file_info(candidate_file_path, f"Input candidate {current_level}-itemsets")

    # Step 3: Execute frequent itemsets finding phase
    def _step_execute_frequent_itemsets_phase() -> bool:
        """Execute frequent itemset finding with error handling."""
        # Determine input paths for current level
        # For level 1: use transaction files only
        # For level 2+: use transaction files (ItemsetSupportCounter needs them to scan)
        #               and candidate file is passed separately via ITEMSET_FILES_ARG
        input_for_level = input_paths

        if not execute_frequent_itemsets_finding(
            input_for_level,
            current_level,
            min_support_count,
            runner_mode,
            hadoop_args,
            owner,
            debug_mode,
        ):
            print(f"{STOP_INDICATOR} Error occurred during frequent itemset finding. Aborting.")
            return False
        return True

    # Step 4: Process frequent itemsets results
    def _step_process_frequent_itemsets_results() -> int:
        """Combine parts and display frequent itemsets results."""
        nonlocal total_frequent_itemsets

        # Combine parts for frequent itemsets with logging
        combine_parts_with_logging = log_combine_parts(combine_parts)
        parts_dir = os.path.join(FREQUENT_ITEMSETS_DIR, f"{PARTS_SUBDIR}_{current_level}")
        combine_parts_with_logging(
            parts_dir,
            f"{FREQUENT_ITEMSETS_FILE_NAME_PREFIX}{FILE_NAME_SEPARATOR}{current_level}"
                f"{FILE_EXTENSION}",
            FREQUENT_ITEMSETS_DIR,
        )

        # Read and display frequent itemsets results from file
        frequent_output_file = fi_file_path(current_level)
        if not is_empty_file(frequent_output_file):
            with open(frequent_output_file, 'r', encoding="utf-8") as f:
                frequent_itemsets_results = extract_itemsets_and_supports(f)
                level_itemsets = len(frequent_itemsets_results)
                total_frequent_itemsets += level_itemsets

            if frequent_itemsets_results:
                print(format_itemset_summary(frequent_itemsets_results, max_display=5))
                print(
                    f"{COMPLETION_INDICATOR} Found {level_itemsets} frequent "
                    f"{current_level}-itemsets"
                    )
            else:
                print(f"   {WARNING_INDICATOR} No frequent itemsets found")
        else:
            print(f"   {WARNING_INDICATOR} No frequent itemsets found")
            level_itemsets = 0

        return level_itemsets

    # Step 5: Check termination conditions
    def _step_check_termination() -> bool:
        """Check if algorithm should terminate due to no frequent itemsets."""
        if is_empty_file(fi_file_path(current_level)):
            print(
                f"{STOP_INDICATOR} No frequent {current_level}-itemsets found. Algorithm complete!"
                )
            return True
        return False

    # Step 6: Execute candidate generation phase
    def _step_execute_candidate_generation_phase() -> bool:
        """Execute candidate generation based on current level."""
        if current_level == 1:
            return _step_execute_2_itemsets_generation()
        return _step_execute_higher_level_generation()

    # Step 6a: Generate 2-itemset candidates
    def _step_execute_2_itemsets_generation() -> bool:
        """Generate 2-itemset candidates with error handling."""
        print(f"\n{TASK_INDICATOR} Generating candidate 2-itemsets")

        # Generate 2-itemset candidates with error handling
        success, candidates_generated = execute_candidate_2_itemsets_generation(
            fi_file_path(current_level),
            debug_mode,
        )

        if not success:
            print(
                f"{STOP_INDICATOR} Error occurred during 2-itemset candidate generation. Aborting."
                )
            return False

        print(f"{COMPLETION_INDICATOR} Generated {candidates_generated} candidate 2-itemsets")
        return True

    # Step 6b: Generate higher-level candidates
    def _step_execute_higher_level_generation() -> bool:
        """Generate candidate itemsets for levels 3+ with error handling."""
        print(f"\n{TASK_INDICATOR} Generating candidate {current_level + 1}-itemsets")

        # Generate candidate itemsets with output suppression and error handling
        if not execute_candidate_itemsets_generation(
            fi_file_path(current_level),
            current_level + 1,
            runner_mode,
            hadoop_args,
            owner,
            debug_mode,
        ):
            print(
                f"{STOP_INDICATOR} Error occurred during candidate itemsets generation. Aborting."
                )
            return False

        # Combine parts for candidate itemsets with logging
        combine_parts_with_logging = log_combine_parts(combine_parts)
        parts_dir = os.path.join(CANDIDATE_ITEMSETS_DIR, f"{PARTS_SUBDIR}_{current_level + 1}")
        combine_parts_with_logging(
            parts_dir,
            f"{CANDIDATE_ITEMSETS_FILE_NAME_PREFIX}{FILE_NAME_SEPARATOR}{current_level + 1}"
                f"{FILE_EXTENSION}",
            CANDIDATE_ITEMSETS_DIR,
        )

        return True

    # Step 7: Process candidate generation results
    def _step_process_candidate_results() -> bool:
        """Process and validate candidate generation results."""
        # Count candidate itemsets generated
        candidate_file = ci_file_path(current_level + 1)
        if not is_empty_file(candidate_file):
            with open(candidate_file, 'r', encoding="utf-8") as f:
                candidate_count = len([line for line in f if line.strip()])
                if current_level > 1:  # Only show count for higher levels
                    print(
                        f"{COMPLETION_INDICATOR} Generated {candidate_count} candidate "
                        f"{current_level + 1}-itemsets"
                        )
        else:
            print(
                f"{STOP_INDICATOR} No candidates generated for {current_level + 1}-itemsets. "
                f"Algorithm complete!"
                )
            return False

        return True

    # Step 8: Advance to next iteration
    def _step_advance_iteration() -> None:
        """Advance algorithm state to next iteration."""
        nonlocal current_level, current_iteration
        current_level += 1
        current_iteration += 1

    # Step 9: Finalize algorithm results
    def _step_finalize_results(algorithm_start: float) -> None:
        """Combine final results and log algorithm completion."""
        # Final combining step
        print(f"\n{TASK_INDICATOR} Combining all results")
        combine_parts_with_logging = log_combine_parts(combine_parts)
        total_lines = combine_parts_with_logging(
            FREQUENT_ITEMSETS_DIR,
            f"{FREQUENT_ITEMSETS_FILE_NAME_PREFIX}{FILE_EXTENSION}",
        )

        # Log final results
        final_file = os.path.join(
            FREQUENT_ITEMSETS_DIR,
            f"{FREQUENT_ITEMSETS_FILE_NAME_PREFIX}{FILE_EXTENSION}"
        )
        log_file_info(final_file, "Final results file")

        # Algorithm completion summary
        duration = time.time() - algorithm_start
        print("\n" + "-" * 100)
        print(f"{COMPLETION_INDICATOR} Apriori Algorithm completed in {duration:.2f}s")
        print(f"   {STATS_INDICATOR} Total frequent itemsets found: {total_frequent_itemsets}")
        print(f"   {STATS_INDICATOR} Levels processed: {current_level}")
        print(f"   {STATS_INDICATOR} Final result lines: {total_lines}")

    # Main Algorithm Execution Using Step Functions
    # ----------------------------------------------------------------------------------

    algorithm_start = _step_initialize_algorithm()

    while current_iteration < max_iterations:
        # Step 1: Log input files for current iteration
        _step_log_iteration_inputs()

        # Step 2: Execute frequent itemsets finding
        if not _step_execute_frequent_itemsets_phase():
            return

        # Step 3: Process frequent itemsets results
        _step_process_frequent_itemsets_results()

        # Step 4: Check termination conditions
        if _step_check_termination():
            break

        # Step 5: Execute candidate generation
        if not _step_execute_candidate_generation_phase():
            return

        # Step 6: Process candidate results
        if not _step_process_candidate_results():
            break

        # Step 7: Advance to next iteration
        _step_advance_iteration()

    # Step 8: Finalize results
    _step_finalize_results(algorithm_start)

# Logging and formatting utilities
# -------------------------------------------------------------------------------------------------

@contextlib.contextmanager
def suppress_mrjob_output(debug_mode: bool = False):
    """Context manager to suppress MRJob configuration messages."""
    if debug_mode:
        # In debug mode, don't suppress output so we can see MRJob errors
        yield sys.stdout
    else:
        # In normal mode, suppress MRJob output for cleaner logs
        old_stderr = sys.stderr
        old_stdout = sys.stdout
        try:
            # Redirect output to capture MRJob messages
            sys.stderr = StringIO()
            temp_stdout = StringIO()
            sys.stdout = temp_stdout
            yield temp_stdout
        finally:
            # Restore original streams
            sys.stderr = old_stderr
            sys.stdout = old_stdout

def log_operation_start(operation: str, level: int | None = None, **kwargs) -> float:
    """
    Log the start of an operation with timestamp and details.

    Args:
        operation (str): Name of the operation starting
        level (int, optional): Algorithm level if applicable
        **kwargs: Additional context to log

    Returns:
        float: Start time for measuring duration
    """
    level_info = f" (Level {level})" if level is not None else ""
    print(f"{TASK_INDICATOR} {operation}{level_info}")

    if kwargs:
        # More descriptive parameter formatting
        param_descriptions = {
            'min_support': 'Minimum support threshold',
            'runner_mode': 'MapReduce execution mode',
            'max_iterations': 'Maximum algorithm iterations',
            'input_files': 'Input transaction files'
        }

        for key, value in kwargs.items():
            description = param_descriptions.get(key, key)
            print(f"   {STATS_INDICATOR} {description}: {value}")
    print()  # Add spacing after start

    return time.time()

def log_operation_end(
        operation: str, start_time: float, level: int | None = None, **kwargs
        ) -> None:
    """
    Log the completion of an operation with duration and results.

    Args:
        operation (str): Name of the operation that completed
        start_time (float): Start time from log_operation_start
        level (int, optional): Algorithm level if applicable
        **kwargs: Additional results to log
    """
    duration = time.time() - start_time
    level_info = f" (Level {level})" if level is not None else ""

    print(f"{COMPLETION_INDICATOR} Completed {operation}{level_info} in {duration:.2f}s")

    if kwargs:
        for key, value in kwargs.items():
            print(f"   {STATS_INDICATOR} {key}: {value}")

    print()  # Add spacing after completion

def get_file_info(file_path: str) -> dict[str, str | int]:
    """
    Get detailed information about a file for logging.

    Args:
        file_path (str): Path to the file

    Returns:
        dict: File information including size, lines, existence
    """
    if not os.path.exists(file_path):
        return {"exists": False, "size": 0, "lines": 0, "size_mb": "0.00"}

    size = os.path.getsize(file_path)
    size_mb = size / (1024 * 1024)

    # Count lines for text files
    lines = 0
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = sum(1 for _ in f)
    except (UnicodeDecodeError, IOError):
        lines = -1  # Binary file or read error

    return {
        "exists": True,
        "size": size,
        "size_mb": f"{size_mb:.2f}",
        "lines": lines
    }

def log_file_info(file_path: str, description: str = "File") -> None:
    """
    Log detailed information about a file.

    Args:
        file_path (str): Path to the file
        description (str): Description of the file's purpose
    """
    info = get_file_info(file_path)
    if info["exists"]:
        if int(info["lines"]) >= 0:
            print(f"   {FILE_INDICATOR} {description}: {file_path} "
                  f"({info['size_mb']} MB, {info['lines']} lines)")
        else:
            print(f"   {FILE_INDICATOR} {description}: {file_path} ({info['size_mb']} MB, binary)")
    else:
        print(f"   {STOP_INDICATOR} {description}: {file_path} (does not exist)")

def count_itemsets_in_output(output_lines: list[tuple[str, int]]) -> dict[str, int | float]:
    """
    Count and categorize itemsets from MapReduce output.

    Args:
        output_lines: List of (itemset, support) tuples from job output

    Returns:
        dict: Statistics about the itemsets found
    """
    if not output_lines:
        return {"total": 0, "min_support": 0, "max_support": 0, "avg_support": 0}

    supports = [support for _, support in output_lines]
    return {
        "total": len(output_lines),
        "min_support": min(supports),
        "max_support": max(supports),
        "avg_support": sum(supports) / len(supports)
    }

def format_itemset_summary(itemsets: list[tuple[str, int]], max_display: int = 10) -> str:
    """
    Format itemset results for display with summary statistics.

    Args:
        itemsets: List of (itemset, support) tuples
        max_display: Maximum number of itemsets to display

    Returns:
        str: Formatted summary string
    """
    if not itemsets:
        return f"   {WARNING_INDICATOR} No itemsets found"

    stats = count_itemsets_in_output(itemsets)
    summary = [
        f"   {COMPLETION_INDICATOR} Found {stats['total']} frequent itemsets",
        f"   {STATS_INDICATOR} Support range: {stats['min_support']} - {stats['max_support']} "
        f"(avg: {stats['avg_support']:.1f})"
    ]

    if itemsets and max_display > 0:
        summary.append(f"   {STATS_INDICATOR} Top {min(max_display, len(itemsets))} itemsets:")
        # Sort by support (descending) for display
        sorted_itemsets = sorted(itemsets, key=lambda x: x[1], reverse=True)
        for itemset, support in sorted_itemsets[:max_display]:
            summary.append(f"      • {itemset} (support: {support})")

        if len(itemsets) > max_display:
            summary.append(f"      ... and {len(itemsets) - max_display} more")

    return "\n".join(summary)

def log_combine_parts(func):
    """
    Decorator to log file combination operations.

    Args:
        func: The combine_parts function to decorate

    Returns:
        Decorated function that logs before and after combination
    """
    def wrapper(parts_dir: str, output_file: str, output_dir: str | None = None):
        # Count parts files for progress tracking
        part_files = [
            part for part in os.listdir(parts_dir)
            if os.path.isfile(os.path.join(parts_dir, part))
            and not part.startswith('.') and not part.startswith('_')
            ]

        if part_files:
            print(f"   {SUBTASK_INDICATOR} Combining {len(part_files)} output parts "
                  f"into {output_file}")

        # Call the actual function
        lines_written = func(parts_dir, output_file, output_dir)

        # Log results
        if lines_written > 0:
            print(f"   {COMPLETION_INDICATOR} Combined {lines_written} lines"
                  f" from {len(part_files)} parts")
        else:
            print(f"   {WARNING_INDICATOR} No data found in parts files")

        return lines_written

    return wrapper

def print_debug_traceback(debug_mode: bool = False):
    """Print stack trace only if debug mode is enabled."""
    if debug_mode:
        print("\n🐛 Debug stack trace:")
        traceback.print_exc()
        print("🐛 End of stack trace\n")
        print()

def main() -> None:
    """
    Parse command-line arguments and execute frequent itemset mining.

    Handles argument validation, directory cleanup, and orchestrates
    the complete Apriori algorithm execution with user-specified parameters.
    """
    parser = argparse.ArgumentParser(
        description="Run MapReduce job for finding frequent itemsets"
    )

    parser.add_argument(
        "input_files",
        nargs="+",
        help="Input transaction files (at least one required)"
    )

    parser.add_argument(
        MIN_SUPPORT_CMD_ARG,
        type=int,
        default=4,
        help="Minimum support count (default: 4)"
    )

    parser.add_argument(
        RUNNER_CMD_ARG,
        default="inline",
        choices=["inline", "local", "hadoop"],
        help="MapReduce runner mode (default: inline)"
    )

    parser.add_argument(
        MAX_ITERATIONS_CMD_ARG,
        type=int,
        default=100,
        help="Maximum number of iterations (default: 100)"
    )

    parser.add_argument(
        CLEAN_CMD_ARG,
        action="store_true",
        help="Clean output directories before running"
    )

    parser.add_argument(
        HADOOP_ARGS_CMD_ARG,
        nargs="*",
        help=(
            "Additional Hadoop arguments as KEY=VALUE pairs when using hadoop runner "
            "(e.g., hadoop.job.ugi=username mapreduce.job.reduces=2)"
        )
    )

    parser.add_argument(
        OWNER_CMD_ARG,
        help="Owner for Hadoop jobs when using hadoop runner"
    )

    parser.add_argument(
        DEBUG_CMD_ARG,
        action="store_true",
        help="Enable debug mode with detailed error stack traces"
    )

    args = parser.parse_args()

    if args.debug:
        print("🐛 Debug mode enabled - showing detailed error messages and MRJob output")
        print()

    # Clean directories if requested
    if args.clean:
        def clean_level_specific_parts(base_dir: str, start_level: int) -> None:
            """Clean all level-specific parts subdirectories for a given base directory."""
            if os.path.exists(base_dir):
                level = start_level
                while True:
                    parts_subdir = os.path.join(base_dir, f"{PARTS_SUBDIR}_{level}")
                    if os.path.exists(parts_subdir):
                        _refresh_directory(parts_subdir, guaranteed_no_existence=True)
                        level += 1
                    else:
                        break

        # Clean all level-specific parts subdirectories
        clean_level_specific_parts(FREQUENT_ITEMSETS_DIR, 1)
        clean_level_specific_parts(CANDIDATE_ITEMSETS_DIR, 3)

        # Then clean main directories
        _refresh_directory(FREQUENT_ITEMSETS_DIR)
        _refresh_directory(CANDIDATE_ITEMSETS_DIR)

    # Validate input files exist
    input_files: list[str] = []
    input_file: str
    for input_file in args.input_files:
        if not os.path.exists(input_file):
            parser.error(f"Input file does not exist: {input_file}")
        input_files.append(input_file)

    # Run frequent itemsets mining
    frequent_itemsets_mining(
        *input_files,
        min_support_count=args.min_support or DEFAULT_MIN_SUPPORT,
        runner_mode=args.runner or DEFAULT_RUNNER_MODE,
        max_iterations=args.max_iterations or DEFAULT_MAX_ITERATIONS,
        hadoop_args=args.hadoop_args,
        owner=args.owner,
        debug_mode=args.debug,
    )

if __name__ == "__main__":
    main()
