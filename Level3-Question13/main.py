"""
Call MRJob using python code
"""
import os
import argparse
from itertools import combinations
from collections.abc import Callable
from typing import TextIO

from itemset_support_counter import (
    ItemsetSupportCounter,
    MIN_SUPPORT_ARG_NAME,
    ITEMSET_FILES_ARG_NAME,
)

from candidate_generator import (
    CandidateGenerator
)


# Constants for argument names
MIN_SUPPORT_CMD_ARG = "--min-support"
RUNNER_CMD_ARG = "--runner"
MAX_ITERATIONS_CMD_ARG = "--max-iterations"
CLEAN_CMD_ARG = "--clean"

# Default values for command-line arguments
DEFAULT_MIN_SUPPORT = 4
DEFAULT_RUNNER_MODE = "inline"
DEFAULT_MAX_ITERATIONS = 100

# Constants for file and directory names
FREQUENT_ITEMSETS_FILE_NAME_PREFIX = "frequent_itemsets"
CANDIDATE_ITEMSETS_FILE_NAME_PREFIX = "candidate_itemsets"
FILE_NAME_SEPARATOR = "_"
FILE_EXTENSION = ".txt"
FREQUENT_ITEMSETS_DIR = "frequent-itemsets"
CANDIDATE_ITEMSETS_DIR = "candidate-itemsets"
PARTS_SUBDIR = "_previous_parts"

def frequence_itemsets_mining(
    *input_paths: str,
    min_support_count: int = 4,
    runner_mode: str = "inline",
    max_iterations: int = 100,
) -> None:
    """
    Main function to run the MapReduce job for finding frequent itemsets.
    This function initializes the directories and runs the job.
    """
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

    current_level: int = 1
    current_iteration: int = 0
    while current_iteration < max_iterations:
        find_frequent_itemsets(
            *input_paths,
            level=current_level,
            min_support_count=min_support_count,
            runner_mode=runner_mode,
        )
        if is_empty_file(fi_file_path(current_level)):
            print(f"No frequent itemsets found at level {current_level}. Stopping.")
            break
        if current_level == 1:
            generate_candidate_2_itemsets(
                fi_file_path(current_level),
            )
        else:
            generate_candidate_itemsets(
                fi_file_path(current_level),
                level=current_level + 1,
                runner_mode=runner_mode,
            )
        if is_empty_file(ci_file_path(current_level + 1)):
            print(f"No candidate itemsets found for level {current_level + 1}. Stopping.")
            break
        current_level += 1
        current_iteration += 1
        print(f"Completed iteration {current_iteration} for level {current_level}.")
    # Join the "frequent itemsets" files into a single file
    combine_parts(
        FREQUENT_ITEMSETS_DIR,
        f"{FREQUENT_ITEMSETS_FILE_NAME_PREFIX}{FILE_EXTENSION}",
    )

def find_frequent_itemsets(
        *input_paths: str,
        level: int = 1,
        min_support_count: int = 2,
        runner_mode: str = "inline",
        ) -> None:
    """"main"""
    if len(input_paths) == 0:
        raise ValueError("At least one input path must be provided.")
    if level < 1:
        raise ValueError("Level must be at least 1 for frequent itemsets generation.")
    if min_support_count < 1:
        raise ValueError("Minimum support count must be at least 1.")

    parts_dir = os.path.join(FREQUENT_ITEMSETS_DIR, PARTS_SUBDIR)
    _refresh_directory(parts_dir)

    arguments = list(input_paths)  # Add input paths first
    arguments.extend([
        "-r", runner_mode,
        "--output-dir", parts_dir,
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

    job = ItemsetSupportCounter(args = arguments)

    with job.make_runner() as runner:
        runner.run()
        combine_parts(
            parts_dir,
            f"{FREQUENT_ITEMSETS_FILE_NAME_PREFIX}{FILE_NAME_SEPARATOR}{level}{FILE_EXTENSION}",
            FREQUENT_ITEMSETS_DIR,
        )

def generate_candidate_2_itemsets(
    *input_paths: str,
    item_separator: str = " ",
) -> None:
    """Generate candidate 2-itemsets from the input paths."""
    if len(input_paths) == 0:
        raise ValueError("At least one input path must be provided.")

    frequent_one_itemsets: dict[str, int] = {}
    for path in input_paths:
        itemset: list[tuple[str, int]] = []
        try:
            with open(path, "r", encoding="utf-8") as infile:
                itemset = extract_itemsets_and_supports(infile)
        except FileNotFoundError:
            print(f"File not found: {path}")
        except IOError as e:
            print(f"Error reading file {path}: {e}")
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
    with open(output_path, "w", encoding="utf-8") as outfile:
        for item1, item2 in combinations(sorted_frequent_one_itemsets, 2):
            outfile.write(f"{item1}{item_separator}{item2}\n")

def generate_candidate_itemsets(
    *input_paths: str,
    level: int = 3,
    runner_mode: str = "inline",
) -> None:
    """Generate candidate itemsets for the next level."""
    if len(input_paths) == 0:
        raise ValueError("At least one input path must be provided.")
    if level < 3:
        raise ValueError("Level must be at least 3 for candidate itemsets generation.")

    parts_dir = os.path.join(CANDIDATE_ITEMSETS_DIR, PARTS_SUBDIR)
    _refresh_directory(parts_dir)

    arguments = list(input_paths)  # Add input paths first
    arguments.extend([
        "-r", runner_mode,
        "--output-dir", parts_dir,
    ])

    job = CandidateGenerator(args = arguments)

    with job.make_runner() as runner:
        runner.run()
        combine_parts(
            parts_dir,
            f"{CANDIDATE_ITEMSETS_FILE_NAME_PREFIX}{FILE_NAME_SEPARATOR}{level}{FILE_EXTENSION}",
            CANDIDATE_ITEMSETS_DIR,
        )

# Utility functions for file and directory management
# -------------------------------------------------------------------------------------------------

def _refresh_directory(directory: str) -> None:
    """
    Reset the specified directory by removing all files and subdirectories,
    or create it if it does not exist.

    Args:
        directory (str): The directory to reset.
    """
    if os.path.exists(directory):
        for item in os.listdir(directory):
            item_path = os.path.join(directory, item)
            if os.path.isfile(item_path):
                os.remove(item_path)
            elif os.path.isdir(item_path):
                os.rmdir(item_path)
    else:
        os.makedirs(directory)

def combine_parts(
    parts_dir: str, output_file: str, output_dir: str | None = None
) -> None:
    """
    Combine parts of a MapReduce job output into a single file.
    Args:
        input_dir (str): Directory containing the parts to combine.
        output_file (str): Name of the output file to create.
        output_dir (str, optional): Directory to save the combined file. Defaults to None.
    """
    if output_dir is None:
        output_dir = parts_dir

    output_path = os.path.join(output_dir, output_file)

    with open(output_path, "w", encoding="utf-8") as outfile:
        for part in sorted(os.listdir(parts_dir)):  # Sort for consistent order
            part_path = os.path.join(parts_dir, part)
            if os.path.isfile(part_path):
                _process_part_file(part_path, outfile)

def _process_part_file(part_path: str, outfile: TextIO) -> None:
    """
    Process a single part file and write non-empty lines to output.
    """
    with open(part_path, "r", encoding="utf-8") as infile:
        for line in infile:
            line = line.strip()
            if line:  # Only write non-empty lines
                outfile.write(line + "\n")

def extract_itemsets_and_supports(
    buffer: TextIO,
    separator: str = "\t",
) -> list[tuple[str, int]]:
    """
    Read an itemset and its support from a buffer.

    Args:
        buffer (TextIO): The input buffer containing itemset and support.
        separator (str): The separator used to split itemset and support.

    Returns:
        tuple[str, int]: A tuple containing the itemset as a string and its support count.
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
    Check if a file is empty.

    Args:
        file_path (str): The path to the file to check.

    Returns:
        bool: True if the file is empty, False otherwise.
    """
    return os.path.exists(file_path) and os.path.getsize(file_path) == 0

def main() -> None:
    """
    Parse command line arguments and run frequent itemsets mining.
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

    args = parser.parse_args()

    # Clean directories if requested
    if args.clean:
        print("Cleaning output directories...")
        # Clean parts subdirectories first
        frequent_parts_dir = os.path.join(FREQUENT_ITEMSETS_DIR, PARTS_SUBDIR)
        candidate_parts_dir = os.path.join(CANDIDATE_ITEMSETS_DIR, PARTS_SUBDIR)
        if os.path.exists(frequent_parts_dir):
            _refresh_directory(frequent_parts_dir)
        if os.path.exists(candidate_parts_dir):
            _refresh_directory(candidate_parts_dir)
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
    frequence_itemsets_mining(
        *input_files,
        min_support_count=args.min_support or DEFAULT_MIN_SUPPORT,
        runner_mode=args.runner or DEFAULT_RUNNER_MODE,
        max_iterations=args.max_iterations or DEFAULT_MAX_ITERATIONS,
    )

if __name__ == "__main__":
    main()
