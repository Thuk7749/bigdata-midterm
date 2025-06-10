#!/home/khtn_22120363/midterm/.venv/bin/python
"""
MapReduce job for implementing the Apriori algorithm to find frequent itemsets.

This module processes transactional database stored across multiple text files
to find frequent itemsets using the Apriori algorithm with a specified minimum
support threshold provided via command line.
"""
from collections.abc import Iterable

from mrjob.job import MRJob
from mrjob.protocol import RawValueProtocol, JSONProtocol, RawProtocol

# Command-line argument names
MIN_SUPPORT_ARG_NAME = '--min-sup'
ITEMSET_FILES_ARG_NAME = '--itemset-files'

# I/O constants
ITEM_SEPARATOR = " "
TRANSACTION_NAME_ITEMSET_SEPARATOR = "\t"

# Internal constant
INTERNAL_ITEMSET_SEPARATOR = ","

# Default values
DEFAULT_MIN_SUPPORT = 1
DEFAULT_ITEMSET_FILES = []

# pylint: disable=abstract-method
class ItemsetSupportCounter(MRJob):
    """
    MapReduce job to count itemset support for the Apriori algorithm.

    This job processes transaction records stored in multiple text files to count
    the support of itemsets. Can operate in two modes: counting all individual items
    or counting specific itemsets provided via files. Supports filtering by minimum
    support threshold to identify frequent itemsets.

    Input Format:
        - Multiple text files containing transaction records
        - Each line: transaction_id\titem1 item2 item3 ...
        - Transaction ID and itemset separated by tab
        - Items within itemset separated by spaces
        - No duplicate items within a transaction

    Output Format:
        - Key-value pairs: (itemset, support_count)
        - Only includes itemsets meeting minimum support threshold
        - Tab-separated output format

    Example:
        Input:
            "t01\thotdogs buns ketchup"
            "t02\thotdogs buns"
        
        Output with min-support=2:
            "hotdogs\t2"
            "buns\t2"
    """
    INPUT_PROTOCOL = RawValueProtocol
    INTERNAL_PROTOCOL = JSONProtocol
    OUTPUT_PROTOCOL = RawProtocol

    def __init__(self, *args, **kwargs):
        """
        Initialize the MapReduce job with default configuration.

        Sets up minimum support threshold and itemset scanning mode flags.
        """
        super().__init__(*args, **kwargs)
        self.minimum_support: int = DEFAULT_MIN_SUPPORT
        self.scanning_specific_itemsets: bool = False
        self.interested_itemsets: list[frozenset[str]] = []

    def configure_args(self):
        """
        Configure command-line arguments for minimum support and itemset files.

        Adds support for --min-sup argument to specify minimum support threshold
        and --itemset-files argument to provide specific itemsets to count.
        """
        super().configure_args()

        self.add_passthru_arg(
            MIN_SUPPORT_ARG_NAME,
            dest='min_support',
            type=int,
            default=DEFAULT_MIN_SUPPORT,
            help=f'Minimum support threshold for itemsets (default: {DEFAULT_MIN_SUPPORT})',
        )

        self.add_file_arg(
            ITEMSET_FILES_ARG_NAME,
            dest='itemset_files',
            action='append',
            default=[],
            help='Path to itemset files containing the itemsets to be processed',
        )

    def mapper_init(self):
        """
        Initialize mapper with configuration from command-line arguments.

        Loads minimum support threshold and itemsets from specified files
        if provided, setting up the scanning mode accordingly.
        """
        self.minimum_support = self.options.min_support or DEFAULT_MIN_SUPPORT

        self.interested_itemsets = []
        if self.options.itemset_files:
            self.scanning_specific_itemsets = True
            itemset_file: str
            for itemset_file in self.options.itemset_files:
                itemset = load_itemsets_from_file(itemset_file)
                if itemset:
                    self.interested_itemsets.extend(itemset)

    def mapper(self, key: None, value: str):
        """
        Extract itemsets from transaction records and emit support counts.

        Processes each transaction line to extract items and either counts
        specific itemsets (if provided) or counts individual items. Emits
        count of 1 for supported itemsets and 0 for unsupported ones.

        Args:
            key (None): Input key, ignored in processing.
            value (str): Transaction line containing transaction_id\titems.

        Yields:
            tuple: (itemset_string, count) where count is 1 or 0.
        """
        transaction = value.strip()
        parts = transaction.split(TRANSACTION_NAME_ITEMSET_SEPARATOR)
        if len(parts) != 2:
            # Skip malformed lines that do not contain exactly one transaction name and one itemset
            return

        _transaction_name, itemset_str = parts
        items = string_to_itemset(itemset_str, ITEM_SEPARATOR)

        if self.scanning_specific_itemsets:
            # Mode 2: Count specific itemsets provided via files (levels 2+)
            for itemset in self.interested_itemsets:
                if items.issuperset(itemset):
                    # Transaction contains this itemset - emit count of 1
                    yield itemset_to_string(itemset, INTERNAL_ITEMSET_SEPARATOR), 1
                else:
                    # Transaction doesn't contain this itemset - emit count of 0
                    yield itemset_to_string(itemset, INTERNAL_ITEMSET_SEPARATOR), 0
        else:
            # Mode 1: Count all individual items (level 1)
            for item in items:
                yield item, 1

    def combiner(self, key: str, values: Iterable[int]):
        """
        Local aggregation of itemset counts to reduce data transfer.

        Sums up counts for each itemset within a single mapper to minimize
        data transferred between map and reduce phases.

        Args:
            key (str): Itemset string representation.
            values (Iterable[int]): Iterator of count values for the itemset.

        Yields:
            tuple: (itemset_string, total_count) for local aggregation.
        """
        yield key, sum(values)

    def reducer_init(self):
        """
        Initialize reducer with configuration from command-line arguments.

        Reloads minimum support threshold and itemsets from files for
        consistent processing across all reducer instances.
        """
        self.minimum_support = self.options.min_support or DEFAULT_MIN_SUPPORT

        self.interested_itemsets = []
        if self.options.itemset_files:
            self.scanning_specific_itemsets = True
            itemset_file: str
            for itemset_file in self.options.itemset_files:
                itemset = load_itemsets_from_file(itemset_file)
                if itemset:
                    self.interested_itemsets.extend(itemset)

    def reducer(self, key: str, values: Iterable[int]):
        """
        Aggregate itemset counts and filter by minimum support threshold.

        Sums total counts for each itemset across all mappers and outputs
        only those meeting the minimum support requirement.

        Args:
            key (str): Itemset string representation.
            values (Iterable[int]): Iterator of count values from all mappers.

        Yields:
            tuple: (itemset_string, total_count) for frequent itemsets only.
        """
        total_count = sum(values)
        if self.scanning_specific_itemsets:
            output_itemset = change_itemset_separator(
                key, INTERNAL_ITEMSET_SEPARATOR, ITEM_SEPARATOR
                )
            if total_count >= self.minimum_support:
                yield output_itemset, str(total_count)
        else:
            if total_count >= self.minimum_support:
                yield key, str(total_count)

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

def change_itemset_separator(
        itemset_str: str,
        old_separator: str = INTERNAL_ITEMSET_SEPARATOR,
        new_separator: str = ITEM_SEPARATOR
        ) -> str:
    """
    Replace separator in an itemset string representation.

    Args:
        itemset_str (str): String representation of the itemset.
        old_separator (str): Current separator to replace.
        new_separator (str): New separator to use.

    Returns:
        str: Itemset string with updated separator.
    """
    items = itemset_str.split(old_separator)
    return new_separator.join(item.strip() for item in items if item.strip())

def load_itemsets_from_file(file_path: str) -> list[frozenset[str]]:
    """
    Load itemsets from a file with one itemset per line.

    Args:
        file_path (str): Path to file containing itemsets.

    Returns:
        list[frozenset[str]]: List of frozensets representing itemsets.
    """
    itemsets = []
    try:
        with open(file_path, mode='r', encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    itemset = string_to_itemset(line, ITEM_SEPARATOR)
                    if itemset:
                        itemsets.append(itemset)
    except FileNotFoundError:
        pass
    except IOError:
        pass
    return itemsets

if __name__ == "__main__":
    ItemsetSupportCounter.run()
