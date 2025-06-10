#!/home/khtn_22120363/midterm/.venv/bin/python
"""
MapReduce job for performing FULL OUTER JOIN between FoodPrice and FoodQuantity tables.

This module processes database records stored across multiple text files to perform
a FULL OUTER JOIN operation between two tables: FoodPrice and FoodQuantity.
"""
from collections.abc import Iterable

from mrjob.job import MRJob
from mrjob.protocol import RawValueProtocol, JSONProtocol

VALUE_SEPARATOR = " "
FOOD_PRICE_TABLE_NAME = "FoodPrice"
FOOD_QUANTITY_TABLE_NAME = "FoodQuantity"
EMPTY_VALUE = -1
NULL_VALUE = "null"

def combine_values(
        values: Iterable[tuple[int, int]],
        ) -> tuple[int, int] | None:
    """
    Combines up to two value tuples representing price and quantity,
    handling cases where one of the values may be missing.

    Args:
        values (Iterable[tuple[int, int]]):
            An iterable of up to two tuples, each representing (price, quantity). 
            A value may be missing and represented by EMPTY_VALUE.

    Returns:
        out (tuple[int, int] | None): 
            - If the input contains exactly one tuple, returns it as is.
            - If the input contains two tuples, combines them into a single (price, quantity)
            tuple if possible, by filling in missing values from each tuple.
            - Returns None if the input is empty, contains more than two tuples,
            or cannot be combined according to the rules.
    """
    table_values = list(values)
    if len(table_values) > 2 or len(table_values) == 0:
        return None
    if len(table_values) == 1:
        return table_values[0]
    first_value, second_value = table_values
    if (
        first_value[0] == EMPTY_VALUE
        and first_value[1] != EMPTY_VALUE
        and second_value[0] != EMPTY_VALUE
        and second_value[1] == EMPTY_VALUE
    ):
        return first_value[1], second_value[0]
    if (
        first_value[0] != EMPTY_VALUE
        and first_value[1] == EMPTY_VALUE
        and second_value[0] == EMPTY_VALUE
        and second_value[1] != EMPTY_VALUE
    ):
        return first_value[0], second_value[1]
    return None

# pylint: disable=abstract-method
class PriceQuantityCombiner(MRJob):
    """
    MapReduce job to perform FULL OUTER JOIN between FoodPrice and FoodQuantity tables.

    This job processes database records stored in multiple text files to perform
    a FULL OUTER JOIN operation between two tables. Each record contains a table name,
    key, and value. The job combines records with matching keys from both tables,
    including records that exist in only one table (using null for missing values).

    Input Format:
        - Multiple text files containing database records
        - Each line represents one record: table_name key value
        - Table names are either "FoodPrice" or "FoodQuantity"
        - Keys are strings (food item names)
        - Values are integers
        - Elements separated by spaces

    Output Format:
        - Tuples: (key, price_value, quantity_value)
        - One entry for each unique key found across both tables
        - Missing values represented as "null"
        - Space-separated output format

    Example:
        Input files containing:
            "FoodPrice Pizza 8"
            "FoodPrice Burger 6"
            "FoodQuantity Pizza 3"
            "FoodQuantity Cake 2"
        
        Output:
            "Pizza 8 3"        # key exists in both tables
            "Burger 6 null"    # key exists only in FoodPrice
            "Cake null 2"      # key exists only in FoodQuantity
    """
    INPUT_PROTOCOL = RawValueProtocol
    INTERNAL_PROTOCOL = JSONProtocol
    OUTPUT_PROTOCOL = RawValueProtocol

    def mapper(self, key: None, value: str):
        """
        Extract table records and emit key-value pairs for joining.

        Processes each line of database records by parsing the table name,
        key, and value. Records from FoodPrice and FoodQuantity tables are
        emitted with the food item name as key and a tuple indicating which
        table the value belongs to.

        Args:
            key (None): Input key (ignored, always None)
            value (str): A line of text containing "table_name key value"

        Yields:
            out (tuple[str, tuple[int, int]]): (food_item, (price, quantity))
                where missing values are represented as EMPTY_VALUE
        """
        line = value.strip()
        parts = [part.strip() for part in line.split(VALUE_SEPARATOR) if part.strip()]
        if len(parts) != 3:
            # If the line does not contain exactly 3 parts, skip it
            return

        table_name, item_name, value_str = parts
        try:
            item_value = int(value_str)
        except ValueError:
            # If the value is not an integer, skip this entry
            return

        if table_name in (FOOD_PRICE_TABLE_NAME, FOOD_QUANTITY_TABLE_NAME):
            yield item_name, (
                item_value if table_name == FOOD_PRICE_TABLE_NAME else EMPTY_VALUE,
                item_value if table_name == FOOD_QUANTITY_TABLE_NAME else EMPTY_VALUE,
            )

    def combiner(self, key: str, values: Iterable[tuple[int, int]]):
        """
        Local aggregation of table records to reduce data transfer.

        Combines records for the same food item within a single mapper
        to minimize data transferred between map and reduce phases.
        Handles joining price and quantity values when both are present.

        Args:
            key (str): Food item name
            values (Iterable[tuple[int, int]]): Iterator of (price, quantity) tuples

        Yields:
            out (tuple[str, tuple[int, int]]): (food_item, combined_values)
        """
        combined_value = combine_values(values)
        if combined_value is not None:
            yield key, combined_value

    def reducer(self, key: str, values: Iterable[tuple[int, int]]):
        """
        Perform FULL OUTER JOIN for each food item across all mappers.

        Combines price and quantity values for each food item to produce
        the final joined result. Missing values are represented as "null"
        in the output, ensuring all food items from both tables are included.

        Args:
            key (str): Food item name
            values (Iterable[tuple[int, int]]): Iterator of (price, quantity) tuples

        Yields:
            out (tuple[None, str]): (None, "food_item price quantity") formatted output
        """
        item_name = key
        combine_value = combine_values(values)
        if combine_value is not None:
            price, quantity = combine_value
            price_str = str(price) if price != EMPTY_VALUE else NULL_VALUE
            quantity_str = str(quantity) if quantity != EMPTY_VALUE else NULL_VALUE
            yield None, f"{item_name}{VALUE_SEPARATOR}{price_str}{VALUE_SEPARATOR}{quantity_str}"

if __name__ == "__main__":
    PriceQuantityCombiner.run()
