#!/home/khtn_22120363/midterm/.venv/bin/python
"""
MapReduce job for computing global histogram of digital single-channel images.

This module processes digital image data stored across multiple text files to compute
a global histogram showing the frequency distribution of pixel values.
"""
from collections.abc import Iterable

from mrjob.job import MRJob
from mrjob.protocol import RawValueProtocol, JSONProtocol, RawProtocol

PIXEL_SEPARATOR = " "

# pylint: disable=abstract-method
class PixelFrequencyCounter(MRJob):
    """
    MapReduce job to compute global histogram of pixel values in digital images.

    This job processes digital single-channel image data stored in multiple text files.
    Each file contains pixel values representing image rows, with pixels separated by
    spaces, tabs, or newlines. The job computes a histogram showing the frequency
    distribution of all pixel values across the entire image dataset.

    Input Format:
        - Multiple text files containing pixel data
        - Each line represents one row of the image
        - Pixel values are integers in range [0, N]
        - Values separated by spaces

    Output Format:
        - Key-value pairs: (pixel_value, frequency_count)
        - One entry for each unique pixel value found
        - Tab-separated output format

    Example:
        Input files containing:
            "1 2 3 4"
            "4 3 2 1"
        
        Output:
            "1\t2"  # pixel value 1 appears 2 times
            "2\t2"  # pixel value 2 appears 2 times
            "3\t2"  # pixel value 3 appears 2 times
            "4\t2"  # pixel value 4 appears 2 times
    """
    INPUT_PROTOCOL = RawValueProtocol
    INTERNAL_PROTOCOL = JSONProtocol
    OUTPUT_PROTOCOL = RawProtocol

    def mapper(self, key: None, value: str):
        """
        Extract pixel values from image data and emit count pairs.

        Processes each line of image data by splitting on whitespace to extract
        individual pixel values. Each valid integer pixel value is emitted with
        a count of 1 for aggregation in the reduce phase.

        Args:
            key (None): Input key (ignored, always None)
            value (str): A line of text containing space-separated pixel values

        Yields:
            out (tuple[int, int]): (pixel_value, 1) for each valid pixel found
        """
        line = value.strip()
        numbers = line.split(PIXEL_SEPARATOR)
        for number in numbers:
            try:
                pixel_value = int(number)
                yield pixel_value, 1
            except ValueError:
                # Skip non-numeric values (whitespace, invalid characters)
                continue

    def mapper_final(self):
        """
        This ensures the job always emits the pixel value 0.
        
        Yields:
            out (tuple(Literal[0], Literal[0])):
        """
        yield 0, 0

    def combiner(self, key: int, values: Iterable[int]):
        """
        Local aggregation of pixel counts to reduce data transfer.

        Combines counts for the same pixel value within a single mapper
        to minimize data transferred between map and reduce phases.

        Args:
            key (int): Pixel value (integer)
            values (Iterable[int]): Iterator of counts (all 1s from mapper)

        Yields:
            out (tuple[int, int]): (pixel_value, local_sum) for this pixel
        """
        yield key, sum(values)

    def reducer(self, key: int, values: Iterable[int]):
        """
        Aggregate global counts for each pixel value across all mappers.

        Sums up all counts for each pixel value to produce the final
        histogram entry showing total frequency of each pixel value.

        Args:
            key (int): Pixel value (integer)
            values (Iterable[int]): Iterator of counts from all mappers/combiners

        Yields:
            out (tuple[str, str]): (pixel_value, total_count) as tab-separated strings
        """
        yield str(key), str(sum(values))

if __name__ == "__main__":
    PixelFrequencyCounter.run()
