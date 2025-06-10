#!/home/khtn_22120363/midterm/.venv/bin/python
"""
MapReduce job for counting the support of itemsets in transactions.
This module processes transactions to count the occurrences of specified itemsets,
including those with zero occurrences, based on a minimum support threshold.
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
    Count the support of itemsets in a distributed manner.
    """
    INPUT_PROTOCOL = RawValueProtocol
    INTERNAL_PROTOCOL = JSONProtocol
    OUTPUT_PROTOCOL = RawProtocol

    def __init__(self, *args, **kwargs):
        """
        Initialize the MapReduce job for counting itemset support.
        Sets up the minimum support threshold and flags for scanning specific itemsets.
        """
        super().__init__(*args, **kwargs)
        self.minimum_support: int = DEFAULT_MIN_SUPPORT
        self.scanning_specific_itemsets: bool = False
        self.interested_itemsets: list[frozenset[str]] = []

    def configure_args(self):
        """
        Configure command-line arguments for the MapReduce job.

        This method is used to set up any additional command-line options
        that the job might need. Currently, it does not add any specific
        options but can be extended in the future.
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
        Initialize the mapper by resetting the maximum pixel value.

        This method is called before processing any input data to ensure
        that the maximum pixel value starts at zero for each mapper instance.
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
        Yield the occurrence of each item in the transaction
        """
        transaction = value.strip()
        parts = transaction.split(TRANSACTION_NAME_ITEMSET_SEPARATOR)
        if len(parts) != 2:
            # Skip malformed lines that do not contain exactly one transaction name and one itemset
            return

        _transaction_name, itemset_str = parts
        items = string_to_itemset(itemset_str, ITEM_SEPARATOR)
        if self.scanning_specific_itemsets:
            for itemset in self.interested_itemsets:
                if items.issuperset(itemset):
                    # Emit the itemset with a count of 1 if it is supported
                    yield itemset_to_string(itemset, INTERNAL_ITEMSET_SEPARATOR), 1
                else:
                    # Emit the itemset with a count of 0 if it is not supported
                    yield itemset_to_string(itemset, INTERNAL_ITEMSET_SEPARATOR), 0

        else:
            for item in items:
                # Emit each item with a count of 1
                yield item, 1

    def combiner(self, key: str, values: Iterable[int]):
        """
        Local aggregation of itemset counts to reduce data transfer.
        """
        yield key, sum(values)

    def reducer_init(self):
        """
        Initialize the reducer by resetting the interested itemsets and minimum support.

        This method is called before processing any input data to ensure
        that the reducer starts with a clean state for each run.
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
        Aggregate the counts for each itemset or item and yield the total count.
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

def change_itemset_separator(
        itemset_str: str,
        old_separator: str = INTERNAL_ITEMSET_SEPARATOR,
        new_separator: str = ITEM_SEPARATOR
        ) -> str:
    """
    Change the separator in a string representation of an itemset.

    Args:
        itemset_str (str): A string representation of the itemset.
        new_separator (str): The new separator to use.

    Returns:
        str: The itemset string with the new separator.
    """
    items = itemset_str.split(old_separator)
    return new_separator.join(item.strip() for item in items if item.strip())

def load_itemsets_from_file(file_path: str) -> list[frozenset[str]]:
    """
    Load itemsets from a file, where each line contains a serialized itemset.

    Args:
        file_path (str): Path to the file containing itemsets.

    Returns:
        list[frozenset[str]]: A list of frozensets representing the itemsets.
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
