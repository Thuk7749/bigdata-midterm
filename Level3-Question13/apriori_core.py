"""
Core MapReduce functions and utilities for the Apriori algorithm implementation.

This module contains the essential MapReduce operations and utility functions
for frequent itemset mining, separated from logging and orchestration logic.
It provides clean, reusable components for:

- Core MapReduce job execution (frequent itemset finding, candidate generation)
- File and directory management utilities
- Data parsing and validation functions
- Constants for file naming and directory structure

The module is designed to be logging-agnostic, focusing purely on the
computational aspects of the Apriori algorithm.
"""
import os
from itertools import combinations
from typing import TextIO

from itemset_support_counter import (
    ItemsetSupportCounter,
    MIN_SUPPORT_ARG_NAME,
    ITEMSET_FILES_ARG_NAME,
)

from candidate_generator import (
    CandidateGenerator
)

from decimal_support_converter import (
    DecimalSupportConverter,
    MIN_SUPPORT_DECIMAL_ARG_NAME,
)

# Constants for file and directory names
FREQUENT_ITEMSETS_FILE_NAME_PREFIX = "frequent_itemsets"
CANDIDATE_ITEMSETS_FILE_NAME_PREFIX = "candidate_itemsets"
FILE_NAME_SEPARATOR = "_"
FILE_EXTENSION = ".txt"
FREQUENT_ITEMSETS_DIR = "frequent-itemsets"
CANDIDATE_ITEMSETS_DIR = "candidate-itemsets"
PARTS_SUBDIR = "_parts"

# Core MapReduce functions
# -------------------------------------------------------------------------------------------------

def find_min_support_count(
        *input_paths: str,
        min_support_decimal: float = 0.5,
        runner_mode: str = "inline",
        hadoop_args: list[str] | None = None,
        owner: str | None = None,
        ) -> int:
    """
    Convert decimal support to actual support count using MapReduce.

    Executes the DecimalSupportConverter MapReduce job to count total transactions
    and calculate the minimum support count by multiplying decimal support by
    total transaction count and flooring the result.

    Args:
        *input_paths (str): Transaction file paths for processing.
        min_support_decimal (float): Minimum decimal support threshold (default: 0.5).
        runner_mode (str): MapReduce execution mode (default: "inline").
        hadoop_args (list[str], optional): Additional Hadoop arguments to pass to MRJob.
        owner (str, optional): Owner for Hadoop jobs when using hadoop runner.

    Returns:
        int: Minimum support count calculated as floor(min_support_decimal * total_transactions).

    Raises:
        ValueError: If input validation fails for paths or decimal support.
        RuntimeError: If MapReduce job fails or produces no output.
    """
    if len(input_paths) == 0:
        raise ValueError("At least one input path must be provided.")
    if not 0.0 <= min_support_decimal <= 1.0:
        raise ValueError("Minimum decimal support must be between 0.0 and 1.0.")

    arguments = list(input_paths)  # Add input paths first
    arguments.extend([
        "-r", runner_mode,
        "--cat-output",
        MIN_SUPPORT_DECIMAL_ARG_NAME, str(min_support_decimal),
    ])

    # Add hadoop-specific arguments if provided and using hadoop runner
    if hadoop_args and runner_mode == "hadoop":
        # Convert KEY=VALUE pairs to -D KEY=VALUE format
        hadoop_formatted_args = []
        for arg in hadoop_args:
            hadoop_formatted_args.extend(["-D", arg])
        arguments.extend(hadoop_formatted_args)

    # Add owner argument if provided and using hadoop runner
    if owner and runner_mode == "hadoop":
        arguments.extend(["--owner", owner])

    job = DecimalSupportConverter(args=arguments)

    try:
        with job.make_runner() as runner:
            runner.run()
            # Get the output directly from the job results
            for line in runner.cat_output():
                line = line.strip()
                if line:
                    return int(line)
    except Exception as e:
        raise RuntimeError(f"MapReduce job failed: {e}") from e

    raise RuntimeError("MapReduce job produced no output.")

def find_frequent_itemsets(
        *input_paths: str,
        level: int = 1,
        min_support_count: int = 2,
        runner_mode: str = "inline",
        hadoop_args: list[str] | None = None,
        owner: str | None = None,
        ) -> None:
    """
    Find frequent itemsets at a specific level using MapReduce.

    Executes the ItemsetSupportCounter MapReduce job to identify itemsets
    meeting the minimum support threshold at the specified level.

    Args:
        *input_paths (str): Transaction file paths for processing.
        level (int): Current itemset size level (default: 1).
        min_support_count (int): Minimum support threshold (default: 2).
        runner_mode (str): MapReduce execution mode (default: "inline").
        hadoop_args (list[str], optional): Additional Hadoop arguments to pass to MRJob.
        owner (str, optional): Owner for Hadoop jobs when using hadoop runner.

    Raises:
        ValueError: If input validation fails for paths, level, or support count.
    """
    if len(input_paths) == 0:
        raise ValueError("At least one input path must be provided.")
    if level < 1:
        raise ValueError("Level must be at least 1 for frequent itemsets generation.")
    if min_support_count < 1:
        raise ValueError("Minimum support count must be at least 1.")

    parts_dir = os.path.join(FREQUENT_ITEMSETS_DIR, f"{PARTS_SUBDIR}_{level}")
    _refresh_directory(
        parts_dir,
        guaranteed_no_existence= runner_mode == "hadoop",
        )

    # Format output directory path based on runner mode
    if runner_mode == "hadoop":
        output_dir = f"file://{os.path.abspath(parts_dir)}"
    else:
        output_dir = parts_dir

    arguments = list(input_paths)  # Add input paths first
    arguments.extend([
        "-r", runner_mode,
        "--output-dir", output_dir,
        "--cat-output",
        MIN_SUPPORT_ARG_NAME, str(min_support_count),
    ])

    if level > 1:
        candidate_file_name = (
            f"{CANDIDATE_ITEMSETS_FILE_NAME_PREFIX}{FILE_NAME_SEPARATOR}{level}{FILE_EXTENSION}"
        )
        candidate_file_path = os.path.join(
            CANDIDATE_ITEMSETS_DIR, candidate_file_name
        )
        arguments.extend([
            ITEMSET_FILES_ARG_NAME, candidate_file_path,
        ])

    # Add hadoop-specific arguments if provided and using hadoop runner
    if hadoop_args and runner_mode == "hadoop":
        # Convert KEY=VALUE pairs to -D KEY=VALUE format
        hadoop_formatted_args = []
        for arg in hadoop_args:
            hadoop_formatted_args.extend(["-D", arg])
        arguments.extend(hadoop_formatted_args)

    # Add owner argument if provided and using hadoop runner
    if owner and runner_mode == "hadoop":
        arguments.extend(["--owner", owner])

    job = ItemsetSupportCounter(args = arguments)

    with job.make_runner() as runner:
        runner.run()

def generate_candidate_2_itemsets(
    *input_paths: str,
    item_separator: str = " ",
) -> int:
    """
    Generate 2-itemset candidates from frequent 1-itemsets.

    Creates all possible 2-item combinations from frequent 1-itemsets
    using a combinatorial approach, avoiding MapReduce overhead for
    this simple case.

    Args:
        *input_paths (str): Paths to frequent 1-itemset files.
        item_separator (str): Separator between items (default: space).

    Returns:
        int: Number of candidate itemsets generated.

    Raises:
        ValueError: If no input paths provided or inconsistent support values found.
        FileNotFoundError: If any of the input files cannot be found.
        IOError: If there's an error reading any of the input files.
    """
    if len(input_paths) == 0:
        raise ValueError("At least one input path must be provided.")

    frequent_one_itemsets: dict[str, int] = {}
    for path in input_paths:
        itemset: list[tuple[str, int]] = []
        try:
            with open(path, "r", encoding="utf-8") as infile:
                itemset = extract_itemsets_and_supports(infile)
        except FileNotFoundError as e:
            raise FileNotFoundError(f"File not found: {path}") from e
        except IOError as e:
            raise IOError(f"Error reading file {path}: {e}") from e
        for item, support in itemset:
            if frequent_one_itemsets.get(item) and frequent_one_itemsets[item] != support:
                raise ValueError(
                    f"Item '{item}' has inconsistent support values: "
                    f"{frequent_one_itemsets[item]} and {support}."
                )
            frequent_one_itemsets[item] = support

    output_path = os.path.join(
        CANDIDATE_ITEMSETS_DIR,
        f"{CANDIDATE_ITEMSETS_FILE_NAME_PREFIX}{FILE_NAME_SEPARATOR}2{FILE_EXTENSION}"
        )
    if not os.path.exists(CANDIDATE_ITEMSETS_DIR):
        os.makedirs(CANDIDATE_ITEMSETS_DIR)

    sorted_frequent_one_itemsets = list(sorted(
        frequent_one_itemsets.keys()
    ))

    candidates_generated = 0
    with open(output_path, "w", encoding="utf-8") as outfile:
        for item1, item2 in combinations(sorted_frequent_one_itemsets, 2):
            outfile.write(f"{item1}{item_separator}{item2}\n")
            candidates_generated += 1

    return candidates_generated

def generate_candidate_itemsets(
    *input_paths: str,
    level: int = 3,
    runner_mode: str = "inline",
    hadoop_args: list[str] | None = None,
    owner: str | None = None,
) -> None:
    """
    Generate candidate itemsets for levels 3 and above using MapReduce.

    Executes the CandidateGenerator MapReduce job to create candidate
    itemsets with proper subset validation and pruning according to
    the Apriori principle.

    Args:
        *input_paths (str): Paths to frequent itemset files from previous level.
        level (int): Target itemset size level (default: 3).
        runner_mode (str): MapReduce execution mode (default: "inline").
        hadoop_args (list[str], optional): Additional Hadoop arguments to pass to MRJob.
        owner (str, optional): Owner for Hadoop jobs when using hadoop runner.

    Raises:
        ValueError: If no input paths provided or level is less than 3.
    """
    if len(input_paths) == 0:
        raise ValueError("At least one input path must be provided.")
    if level < 3:
        raise ValueError("Level must be at least 3 for candidate itemsets generation.")

    parts_dir = os.path.join(CANDIDATE_ITEMSETS_DIR, f"{PARTS_SUBDIR}_{level}")
    _refresh_directory(
        parts_dir,
        guaranteed_no_existence= runner_mode == "hadoop",
        )

    # Format output directory path based on runner mode
    if runner_mode == "hadoop":
        output_dir = f"file://{os.path.abspath(parts_dir)}"
    else:
        output_dir = parts_dir

    arguments = list(input_paths)  # Add input paths first
    arguments.extend([
        "-r", runner_mode,
        "--cat-output",
        "--output-dir", output_dir,
    ])

    # Add hadoop-specific arguments if provided and using hadoop runner
    if hadoop_args and runner_mode == "hadoop":
        # Convert KEY=VALUE pairs to -D KEY=VALUE format
        hadoop_formatted_args = []
        for arg in hadoop_args:
            hadoop_formatted_args.extend(["-D", arg])
        arguments.extend(hadoop_formatted_args)

    # Add owner argument if provided and using hadoop runner
    if owner and runner_mode == "hadoop":
        arguments.extend(["--owner", owner])

    job = CandidateGenerator(args = arguments)

    with job.make_runner() as runner:
        runner.run()

# Utility functions for file and directory management
# -------------------------------------------------------------------------------------------------

def _refresh_directory(directory: str, guaranteed_no_existence: bool = False) -> None:
    """
    Reset directory by removing all contents or create if non-existent.

    Args:
        directory (str): Directory path to reset or create.
        guaranteed_no_existence (bool):
            If True, ensure directory does not exist after cleanup.
    """
    if os.path.exists(directory):
        for item in os.listdir(directory):
            item_path = os.path.join(directory, item)
            if os.path.isfile(item_path):
                os.remove(item_path)
            elif os.path.isdir(item_path):
                os.rmdir(item_path)
        if guaranteed_no_existence:
            os.rmdir(directory)
    elif not guaranteed_no_existence:
        os.makedirs(directory)

def combine_parts(
    parts_dir: str, output_file: str, output_dir: str | None = None
) -> int:
    """
    Combine MapReduce output parts into a single consolidated file.

    Args:
        parts_dir (str): Directory containing MapReduce output parts.
        output_file (str): Name of the consolidated output file.
        output_dir (str, optional): Output directory (defaults to parts_dir).
        
    Returns:
        int: Number of lines written to the output file.
    """
    if output_dir is None:
        output_dir = parts_dir

    output_path = os.path.join(output_dir, output_file)

    # Get parts files to process
    part_files = [
        part for part in os.listdir(parts_dir)
        if os.path.isfile(os.path.join(parts_dir, part))
          and not part.startswith('.')
          and not part.startswith('_')
    ]

    lines_written = 0
    with open(output_path, "w", encoding="utf-8") as outfile:
        for part in sorted(part_files):  # Sort for consistent order
            part_path = os.path.join(parts_dir, part)
            part_lines = _process_part_file(part_path, outfile)
            lines_written += part_lines

    return lines_written

def _process_part_file(part_path: str, outfile: TextIO) -> int:
    """
    Process individual MapReduce part file and write non-empty lines to output.

    Args:
        part_path (str): Path to the part file to process.
        outfile (TextIO): Output file handle for writing consolidated results.

    Returns:
        int: Number of lines written from this part file.
    """
    lines_written = 0
    with open(part_path, "r", encoding="utf-8") as infile:
        for line in infile:
            line = line.strip()
            if line:  # Only write non-empty lines
                outfile.write(line + "\n")
                lines_written += 1
    return lines_written

def extract_itemsets_and_supports(
    buffer: TextIO,
    separator: str = "\t",
) -> list[tuple[str, int]]:
    """
    Parse itemsets and support counts from input buffer.

    Args:
        buffer (TextIO): Input buffer containing itemset-support pairs.
        separator (str): Separator between itemset and support (default: tab).

    Returns:
        list[tuple[str, int]]: List of (itemset_string, support_count) tuples.
    """
    results = []
    for line in buffer:
        line = line.strip()
        if not line:
            continue
        parts = line.split(separator)
        if len(parts) != 2:
            continue
        itemset_str, support_str = parts
        support = int(support_str) if support_str.isdigit() else 0
        results.append((itemset_str, support))
    return results

def is_empty_file(file_path: str) -> bool:
    """
    Check if a file exists and is empty.

    Args:
        file_path (str): Path to the file to check.

    Returns:
        bool: True if file exists and is empty, False otherwise.
    """
    return os.path.exists(file_path) and os.path.getsize(file_path) == 0
