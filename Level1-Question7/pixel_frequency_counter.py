#!/home/khtn_22120363/midterm/.venv/bin/python
"""
MapReduce job for computing complete histogram of digital single-channel images.

This module processes digital image data stored across multiple text files to compute
a complete histogram showing the frequency distribution of ALL possible pixel values
in the range [0, N], including those with zero occurrences.
"""
from collections.abc import Iterable

from mrjob.job import MRJob
from mrjob.protocol import RawValueProtocol, JSONProtocol, RawProtocol

PIXEL_SEPARATOR = " "

MINIMUM_DIGIT_KEY = 10

def pad_number(number: int, min_digits: int = MINIMUM_DIGIT_KEY) -> str:
    """
    Pad a number with leading zeros to ensure it has at least `min_digits` digits.

    Args:
        number (int): The number to pad.
        min_digits (int): Minimum number of digits the output should have.

    Returns:
        str: The padded number as a string.
    """
    return str(number).zfill(min_digits)

# pylint: disable=abstract-method
class PixelFrequencyCounter(MRJob):
    """
    MapReduce job to compute complete histogram of pixel values in digital images.

    This job processes digital single-channel image data stored in multiple text files
    and ensures ALL possible pixel values from 0 to the maximum found value are 
    included in the output, even if their count is zero. This creates a complete 
    histogram with all bins in the pixel value range.

    Input Format:
        - Multiple text files containing pixel data
        - Each line represents one row of the image
        - Pixel values are integers in range [0, N] (you don't have to provide N)
        - Values separated by spaces, tabs, or newlines

    Output Format:
        - Key-value pairs for ALL values from 0 to max_value_found
        - Format: (pixel_value, frequency_count)
        - Includes zero-count entries for missing pixel values
        - Tab-separated output format

    Example:
        Input files containing:
            "0 2 7 2"
            "7 5 0"
            "2 5 5"
        
        Output (complete range 0-7):
            "0\t2"  # pixel value 0 appears 2 times
            "1\t0"  # pixel value 1 appears 0 times (missing)
            "2\t3"  # pixel value 2 appears 3 times
            "3\t0"  # pixel value 3 appears 0 times (missing)
            "4\t0"  # pixel value 4 appears 0 times (missing)
            "5\t3"  # pixel value 5 appears 3 times
            "6\t0"  # pixel value 6 appears 0 times (missing)
            "7\t2"  # pixel value 7 appears 2 times
    """
    INPUT_PROTOCOL = RawValueProtocol
    INTERNAL_PROTOCOL = JSONProtocol
    OUTPUT_PROTOCOL = RawProtocol

    def __init__(self, *args, **kwargs):
        """
        Initialize the MapReduce job with pixel value tracking.

        Sets up instance variable to track the maximum pixel value
        encountered across all input data for complete histogram generation.
        """
        super().__init__(*args, **kwargs)
        self.maximum_value = 0

    def mapper(self, key: None, value: str):
        """
        Extract pixel values and track maximum value for complete histogram.

        Processes each line of image data by splitting on whitespace to extract
        individual pixel values. Each valid integer pixel value is emitted with
        a count of 1, and the maximum value seen is tracked for complete range output.

        Args:
            key (None): Input key (ignored) 
            value (str): A line of text containing space-separated pixel values

        Yields:
            out (tuple[str, int]): (padded_pixel_value, 1) for each valid pixel found
        """
        line = value.strip()
        numbers = line.split(PIXEL_SEPARATOR)
        for number in numbers:
            try:
                pixel_value = int(number)
                self.maximum_value = max(self.maximum_value, pixel_value)
                yield pad_number(pixel_value), 1
            except ValueError:
                # Skip non-numeric values (whitespace, invalid characters)
                continue

    def mapper_final(self):
        """
        Ensure complete histogram by emitting zero counts for all possible values.

        After processing all input lines, this method emits zero counts for every
        possible pixel value from 0 to the maximum value found. This guarantees
        that the final output includes all bins in the histogram range.

        Yields:
            out (tuple[str, int]): (padded_pixel_value, 0) for each value in range [0, max_value]
        """
        for i in range(self.maximum_value + 1):
            yield pad_number(i), 0

    def combiner(self, key: str, values: Iterable[int]):
        """
        Local aggregation of pixel counts to reduce data transfer.

        Combines counts for the same pixel value within a single mapper
        to minimize data transferred between map and reduce phases.
        Handles both actual counts (1s) and placeholder zeros.

        Args:
            key (str): Padded pixel value as string (e.g., "0000000001")
            values (Iterable[int]): Iterator of counts (1s from mapper, 0s from mapper_final)

        Yields:
            out (tuple[str, int]): (padded_pixel_value, local_sum) for this pixel
        """
        yield key, sum(values)

    def reducer(self, key: str, values: Iterable[int]):
        """
        Aggregate global counts for each pixel value to create complete histogram.

        Sums up all counts for each pixel value to produce the final complete
        histogram entry. This includes entries with zero counts for pixel values
        that don't appear in the input data but fall within the range [0, N].

        Args:
            key (str): Padded pixel value as string (e.g., "0000000001")
            values (Iterable[int]): Iterator of counts from all mappers/combiners

        Yields:
            tuple[str, str]: (pixel_value, total_count) as tab-separated strings
        """
        yield str(int(key)), str(sum(values))

if __name__ == "__main__":
    PixelFrequencyCounter.run()
