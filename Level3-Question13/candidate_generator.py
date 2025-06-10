#!/home/khtn_22120363/midterm/.venv/bin/python
"""
MapReduce job for generating candidate itemsets based on frequent itemsets.
This module processes frequent itemsets to generate candidate itemsets
that may potentially become frequent in the next iteration.
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
    MapReduce job for generating candidate itemsets based on the already frequent itemsets.
    """
    INPUT_PROTOCOL = RawValueProtocol
    INTERNAL_PROTOCOL = JSONProtocol
    OUTPUT_PROTOCOL = RawValueProtocol # ignore the key

    def steps(self):
        """
        Define the steps for the MapReduce job.

        This method specifies the sequence of mapper and reducer functions
        that will be executed during the MapReduce process.
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
        Yield the (prefix, postfix) pairs for each frequent itemset in the transaction.
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
        Reduce the (prefix, postfix) pairs to generate candidate itemsets.
        """
        postfix_support_dict: dict[str, int] = {}
        for pair in postfix_support_pairs:
            postfix, support = pair.split(IN_ITEMSET_SUPPORT_SEPARATOR)

            # Generate the original frequent itemset generating this prefix-postfix pair
            yield (
                f"{prefix}{ITEM_SEPARATOR}{postfix}",
                f"{IN_ITEMSET_SUPPORT_SEPARATOR}{support}",
            )

            # if postfix_support_dict.get(postfix) is None or \
            #     postfix_support_dict[postfix] > int(support):
            #     postfix_support_dict[postfix] = int(support)

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
        Identity mapper that yields the input key-value pair as is.
        This is used to pass through the input data without modification.
        """
        yield key, value

    def subset_validating_reducer(
        self, _candidate_subset: str, candidates_with_support: Iterable[str]
    ):
        """
        Validate if any subset of the candidates exists in the original frequent itemsets.
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
        Prune candidates.
        """
        supports_list = list(supports)
        is_pruned = len(supports_list) == 0 or any(
            support == UNEXISTED_SUPPORT for support in supports_list
        )
        if not is_pruned:
            yield None, candidate

def itemset_to_string(itemset: Iterable[str], separator: str = ITEM_SEPARATOR) -> str:
    """
    Convert an itemset (set of items) to a string representation.

    Args:
        itemset (Iterable[str]): An iterable containing items in the itemset.

    Returns:
        str: A string representation of the itemset, with items separated by spaces.
    """
    return separator.join(sorted(itemset))

def string_to_itemset(itemset_str: str, separator: str = ITEM_SEPARATOR) -> frozenset[str]:
    """
    Convert a string representation of an itemset back to a frozenset.

    Args:
        itemset_str (str): A string representation of the itemset.

    Returns:
        frozenset[str]: A frozenset containing the items in the itemset.
    """
    items = itemset_str.strip().split(separator)
    return frozenset(item.strip() for item in items if item.strip())

def reorder_items(itemset_str: str, separator: str = ITEM_SEPARATOR) -> str:
    """
    Reorder items in an itemset string to ensure consistent ordering.

    This function sorts the items in the itemset string and returns the reordered string.
    If `reporting_count` is True, it also returns the count of items in the itemset.

    Args:
        itemset_str (str): A string representation of the itemset.
        reporting_count (bool): Whether to return the count of items in the itemset.

    Returns:
        out (str | tuple[str, int]):
            A string with items sorted and separated by ITEM_SEPERATOR,
            or a tuple containing the sorted string and the count of items.
    """
    items = itemset_str.strip().split(separator)
    return ITEM_SEPARATOR.join(sorted(items))

def split_ordered_itemset(
        itemset_str, postfix_size: int, item_separator: str = ITEM_SEPARATOR
        ) -> tuple[str, str]:
    """
    Split an itemset string into a prefix and postfix based on the first group size.
    Assumes the itemset is already in a consistent order.

    Args:
        itemset_str (str): A string representation of the itemset.
        first_group_size (int): The size of the first group to extract as prefix.

    Returns:
        tuple[str, str]: A tuple containing the prefix and postfix itemsets.
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
