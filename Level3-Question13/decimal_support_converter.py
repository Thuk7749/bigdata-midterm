#!/home/khtn_22120363/midterm/.venv/bin/python
"""
MapReduce job for converting decimal support to actual support counts.

This module processes transaction databases to count the total number of transactions,
then multiplies decimal support values by this count to convert decimal support
to actual support counts for itemsets.
"""
import math
from collections.abc import Iterable

from mrjob.job import MRJob
from mrjob.protocol import RawValueProtocol, JSONProtocol

# Command-line argument names
MIN_SUPPORT_DECIMAL_ARG_NAME = '--min-sup-decimal'

# I/O constants
TRANSACTION_NAME_ITEMSET_SEPARATOR = "\t"

# Default values
DEFAULT_MIN_SUPPORT_DECIMAL = 0.5

# pylint: disable=abstract-method
class DecimalSupportConverter(MRJob):
    """
    MapReduce job to convert decimal support to actual support counts.

    This job processes transaction files to count the total number of transactions,
    which can then be used to convert decimal support values to actual support counts
    by multiplying decimal support by the total transaction count.

    Input Format:
        - Multiple text files containing transaction records
        - Each line: transaction_id\titem1 item2 item3 ...
        - Transaction ID and itemset separated by tab
        - Items within itemset separated by spaces

    Output Format:
        - Support count calculated as floor(min_sup_decimal * total_transactions)
        - Raw value output format

    Example:
        Input:
            "t01\tbread milk eggs"
            "t02\tbread butter"
        
        Output with min-sup-decimal=0.5:
            "1"
    """
    INPUT_PROTOCOL = RawValueProtocol
    INTERNAL_PROTOCOL = JSONProtocol
    OUTPUT_PROTOCOL = RawValueProtocol

    def __init__(self, *args, **kwargs):
        """
        Initialize the MapReduce job with default configuration.

        Sets up minimum decimal support threshold for potential use.
        """
        super().__init__(*args, **kwargs)
        self.minimum_decimal_support: float = DEFAULT_MIN_SUPPORT_DECIMAL

    def configure_args(self):
        """
        Configure command-line arguments for minimum decimal support threshold.

        Adds support for --min-sup-decimal argument to specify minimum decimal
        support threshold for itemsets.
        """
        super().configure_args()

        self.add_passthru_arg(
            MIN_SUPPORT_DECIMAL_ARG_NAME,
            dest='min_support_decimal',
            type=float,
            default=DEFAULT_MIN_SUPPORT_DECIMAL,
            help=(
                f'Minimum decimal support threshold for itemsets '
                f'(default: {DEFAULT_MIN_SUPPORT_DECIMAL})'
            ),
        )

    def mapper(self, key: None, value: str):
        """
        Count transaction records to determine total transaction count.

        Processes each transaction line and emits a count of 1 to calculate
        the total number of transactions in the database. This count can then
        be used to convert decimal support to actual support counts.

        Args:
            key (None): Input key, ignored in processing.
            value (str): Transaction line containing transaction_id\titems.

        Yields:
            tuple: ("total_transactions", 1) for each valid transaction.
        """
        transaction = value.strip()
        parts = transaction.split(TRANSACTION_NAME_ITEMSET_SEPARATOR)
        if len(parts) != 2:
            # Skip malformed lines that do not contain exactly one transaction name and one itemset
            return

        # Count each valid transaction
        yield "total_transactions", 1

    def combiner(self, key: str, values: Iterable[int]):
        """
        Local aggregation of transaction counts to reduce data transfer.

        Sums up transaction counts within a single mapper to minimize
        data transferred between map and reduce phases.

        Args:
            key (str): Category ("total_transactions").
            values (Iterable[int]): Iterator of count values (1s).

        Yields:
            tuple: (category, total_count) for local aggregation.
        """
        yield key, sum(values)

    def reducer_init(self):
        """
        Initialize reducer with configuration from command-line arguments.

        Reloads minimum decimal support threshold for consistent processing
        across all reducer instances.
        """
        self.minimum_decimal_support = (
            self.options.min_support_decimal or DEFAULT_MIN_SUPPORT_DECIMAL
        )

    def reducer(self, key: str, values: Iterable[int]):
        """
        Aggregate transaction counts and calculate support count from decimal support.

        Sums total transaction counts across all mappers and calculates the actual
        support count by multiplying the decimal support threshold by the total
        transaction count and flooring the result.

        Args:
            key (str): Category ("total_transactions").
            values (Iterable[int]): Iterator of count values from all mappers.

        Yields:
            str: Support count as floor(min_sup_decimal * total_transactions).
        """
        total_count = sum(values)
        support_count = math.floor(self.minimum_decimal_support * total_count)
        yield None, str(support_count)

if __name__ == "__main__":
    DecimalSupportConverter.run()
