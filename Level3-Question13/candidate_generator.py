#!/home/khtn_22120363/midterm/.venv/bin/python
"""
MapReduce job for generating candidate itemsets for the Apriori algorithm.

This module processes frequent itemsets to generate candidate itemsets for
the next iteration of the Apriori algorithm, implementing subset validation
and pruning to ensure all candidates have frequent subsets.
"""
from collections.abc import Iterable
from typing import Any
from itertools import combinations

from mrjob.job import MRJob
from mrjob.protocol import RawValueProtocol, JSONProtocol
from mrjob.step import MRStep

# I/O constants
ITEM_SEPARATOR = " "
ITEMSET_SUPPORT_SEPARATOR = "\t"

# Internal constants
IN_ITEMSET_SUPPORT_SEPARATOR = ":"
UNEXISTED_SUPPORT = -1

# pylint: disable=abstract-method
class CandidateGenerator(MRJob):
    """
    MapReduce job to generate candidate itemsets for the Apriori algorithm.

    This job processes frequent itemsets from the previous iteration to generate
    candidate itemsets for the next level. Implements the candidate generation
    phase of Apriori with subset validation and pruning to ensure all generated
    candidates have frequent subsets, reducing computational overhead.

    Input Format:
        - Multiple text files containing frequent itemsets
        - Each line: itemset\tsupport_count
        - Itemset items separated by spaces
        - Tab-separated itemset and support values

    Output Format:
        - Candidate itemsets for next iteration
        - One itemset per line with space-separated items
        - Only candidates with all frequent subsets included

    Example:
        Input:
            "hotdogs buns\t3"
            "hotdogs chips\t2"
            "buns chips\t2"
        
        Output:
            "hotdogs buns chips"  # 3-itemset candidate
    """
    INPUT_PROTOCOL = RawValueProtocol
    INTERNAL_PROTOCOL = JSONProtocol
    OUTPUT_PROTOCOL = RawValueProtocol # ignore the key

    def steps(self):
        """
        Define the three-step MapReduce pipeline for candidate generation.

        Returns:
            list[MRStep]: Sequential steps for prefix-based generation,
                         subset validation, and candidate pruning.
        """
        return [
            MRStep(
                mapper=self.prefix_mapper,
                reducer=self.checking_subsets_generating_reducer,
                ),
            MRStep(
                mapper=self.identical_mapper,
                reducer=self.subset_validating_reducer,
                ),
            MRStep(
                mapper=self.identical_mapper,
                reducer=self.candidate_pruning_reducer,
                ),
        ]

    def prefix_mapper(self, _key: None, value: str):
        """
        Extract prefix-postfix pairs from frequent itemsets for candidate generation.

        Parses frequent itemset records and splits them into prefix and postfix
        components to enable systematic candidate generation in the reducer.

        Args:
            _key (None): Input key, ignored in processing.
            value (str): Frequent itemset line containing itemset\tsupport.

        Yields:
            tuple: (prefix, postfix:support) for candidate generation.
        """
        line = value.strip()
        parts = [part.strip() for part in line.split(ITEMSET_SUPPORT_SEPARATOR) if part.strip()]
        if len(parts) != 2:
            return

        itemset_str, support_str = parts
        if not support_str.isdigit():
            return
        support = int(support_str)

        ordered_itemset_str = reorder_items(itemset_str)
        prefix, postfix = split_ordered_itemset(ordered_itemset_str, postfix_size=1)
        yield prefix, f"{postfix}{IN_ITEMSET_SUPPORT_SEPARATOR}{support}"

    def checking_subsets_generating_reducer(
            self, prefix: str, postfix_support_pairs: Iterable[str]
            ):
        """
        Generate candidate itemsets and their required subsets for validation.

        Combines postfix items sharing the same prefix to create candidates,
        then generates all required subsets that must be frequent for the
        candidate to be valid according to Apriori principle.

        Args:
            prefix (str): Common prefix shared by frequent itemsets.
            postfix_support_pairs (Iterable[str]): Postfix items with support values.

        Yields:
            tuple: (subset, candidate:support) for subset validation phase.
        """
        postfix_support_dict: dict[str, int] = {}
        for pair in postfix_support_pairs:
            postfix, support = pair.split(IN_ITEMSET_SUPPORT_SEPARATOR)

            # Generate the original frequent itemset generating this prefix-postfix pair
            yield (
                f"{prefix}{ITEM_SEPARATOR}{postfix}",
                f"{IN_ITEMSET_SUPPORT_SEPARATOR}{support}",
            )

            # Don't worry, `postfix` should only be appeared once here
            postfix_support_dict[postfix] = int(support)

        prefix_items = string_to_itemset(prefix)
        postfix_items = sorted(postfix_support_dict.keys())

        if len(prefix_items) == 0 or len(postfix_items) < 2:
            # No further (not check yet) subsets needed to be generated
            # Empty prefix only happens when level = 1,
            # and we don't handle that case here, but still check just for safety
            return

        # Edge case: if the prefix has only one item
        if len(prefix_items) == 1:
            # If the prefix has only one item (i.e., original f.i.s are 2-itemsets),
            # No prefix should be used to generate subsets
            # (Because 2 postfix items are more than enough)
            for postfix1, postfix2 in combinations(postfix_items, 2):
                candidate = f"{prefix}{ITEM_SEPARATOR}{postfix1}{ITEM_SEPARATOR}{postfix2}"
                yield (
                    f"{postfix1}{ITEM_SEPARATOR}{postfix2}",
                    f"{candidate}{IN_ITEMSET_SUPPORT_SEPARATOR}{UNEXISTED_SUPPORT}",
                )
            return

        sub_prefix_combinations = combinations(
            prefix_items, len(prefix_items) - 1
        )
        sub_prefix: tuple[str, ...]
        for postfix1, postfix2 in combinations(postfix_items, 2):
            candidate = f"{prefix}{ITEM_SEPARATOR}{postfix1}{ITEM_SEPARATOR}{postfix2}"
            for sub_prefix in sub_prefix_combinations:
                candidate_subset = (
                    f"{itemset_to_string(sub_prefix)}{ITEM_SEPARATOR}"
                    f"{postfix1}{ITEM_SEPARATOR}{postfix2}"
                )
                yield (
                    candidate_subset,
                    f"{candidate}{IN_ITEMSET_SUPPORT_SEPARATOR}{UNEXISTED_SUPPORT}",
                )

    def identical_mapper(self, key: Any, value: Any):
        """
        Pass-through mapper for data transfer between reduce phases.

        Args:
            key (Any): Input key to pass through unchanged.
            value (Any): Input value to pass through unchanged.

        Yields:
            tuple: (key, value) unchanged for next processing step.
        """
        yield key, value

    def subset_validating_reducer(
        self, _candidate_subset: str, candidates_with_support: Iterable[str]
    ):
        """
        Validate candidate subsets against original frequent itemsets.

        Checks if required subsets exist in the frequent itemset collection
        and propagates validation results to candidates for pruning decision.

        Args:
            _candidate_subset (str): Subset that must be frequent.
            candidates_with_support (Iterable[str]): Candidates requiring this subset.

        Yields:
            tuple: (candidate, support_status) for pruning evaluation.
        """
        original_subset_support: int = UNEXISTED_SUPPORT

        # Don't have to use set - Each candidate should only generate each of its subsets once
        candidates: list[str] = []
        for pair in candidates_with_support:
            potential_candidate, support = pair.split(IN_ITEMSET_SUPPORT_SEPARATOR)
            if support != UNEXISTED_SUPPORT:
                original_subset_support = int(support)
            if potential_candidate:
                candidates.append(potential_candidate)
        for candidate in candidates:
            yield candidate, original_subset_support

    def candidate_pruning_reducer(self, candidate: str, supports: Iterable[int]):
        """
        Prune candidates with non-frequent subsets according to Apriori principle.

        Filters out candidates that have any subset missing from frequent
        itemsets, ensuring only valid candidates proceed to support counting.

        Args:
            candidate (str): Candidate itemset to evaluate.
            supports (Iterable[int]): Support status for required subsets.

        Yields:
            tuple: (None, candidate) for candidates passing all subset checks.
        """
        supports_list = list(supports)
        is_pruned = len(supports_list) == 0 or any(
            support == UNEXISTED_SUPPORT for support in supports_list
        )
        if not is_pruned:
            yield None, candidate

def itemset_to_string(itemset: Iterable[str], separator: str = ITEM_SEPARATOR) -> str:
    """
    Convert an itemset to a sorted string representation.

    Args:
        itemset (Iterable[str]): An iterable containing items in the itemset.
        separator (str): Separator to use between items (default: space).

    Returns:
        str: String representation with items sorted and separated.
    """
    return separator.join(sorted(itemset))

def string_to_itemset(itemset_str: str, separator: str = ITEM_SEPARATOR) -> frozenset[str]:
    """
    Parse a string representation back to an itemset frozenset.

    Args:
        itemset_str (str): String representation of the itemset.
        separator (str): Separator used between items (default: space).

    Returns:
        frozenset[str]: Frozenset containing the parsed items.
    """
    items = itemset_str.strip().split(separator)
    return frozenset(item.strip() for item in items if item.strip())

def reorder_items(itemset_str: str, separator: str = ITEM_SEPARATOR) -> str:
    """
    Sort items in an itemset string for consistent ordering.

    Args:
        itemset_str (str): String representation of the itemset.
        separator (str): Separator used between items (default: space).

    Returns:
        str: Itemset string with items sorted alphabetically.
    """
    items = itemset_str.strip().split(separator)
    return ITEM_SEPARATOR.join(sorted(items))

def split_ordered_itemset(
        itemset_str, postfix_size: int, item_separator: str = ITEM_SEPARATOR
        ) -> tuple[str, str]:
    """
    Split an ordered itemset into prefix and postfix components.

    Args:
        itemset_str (str): String representation of the ordered itemset.
        postfix_size (int): Number of items to include in postfix.
        item_separator (str): Separator used between items (default: space).

    Returns:
        tuple[str,str]: Prefix and postfix itemset strings.

    Raises:
        ValueError: If postfix_size is negative.
    """
    if postfix_size < 0:
        raise ValueError("first_group_size must be non-negative")
    items = itemset_str.strip().split(item_separator)
    if len(items) <= postfix_size:
        return "", itemset_str
    prefix_size = len(items) - postfix_size
    prefix = ITEM_SEPARATOR.join(items[:prefix_size])
    postfix = ITEM_SEPARATOR.join(items[prefix_size:])
    return prefix, postfix

if __name__ == "__main__":
    CandidateGenerator.run()
