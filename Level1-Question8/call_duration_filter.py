#!/home/khtn_22120363/midterm/.venv/bin/python
"""
MapReduce job for analyzing telecom call records to identify high STD call users.

This module processes telecom subscriber call records stored across multiple text files
to identify subscribers making more than 60 minutes of STD (long distance) calls,
enabling targeted marketing of STD call packages.
"""
from dataclasses import dataclass
from datetime import datetime
from collections.abc import Iterable

from mrjob.job import MRJob
from mrjob.protocol import RawValueProtocol, JSONProtocol, RawProtocol

# Record and date-time format constants
DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
RECORD_SEPARATOR = "|"

# Minimum duration for a long STD call in seconds
MINIMUM_LONG_CALL_DURATION = 3600

SECONDS_IN_MINUTE = 60

@dataclass(frozen=True)
class CallInfo:
    """
    Represents a single telecom call record with its attributes.

    Attributes:
        calling_number (str): The phone number making the call
        receiving_number (str): The phone number receiving the call
        start_time (datetime): When the call started
        end_time (datetime): When the call ended
        is_std_call (bool): True if this is an STD (long distance) call
    """
    calling_number: str
    receiving_number: str
    start_time: datetime
    end_time: datetime
    is_std_call: bool

    @classmethod
    def from_string(cls, record: str) -> "CallInfo":
        """
        Parses a string record into a CallInfo object.

        Args:
            record (str):
                A string containing call information in the format:
                "calling_number|receiving_number|start_time|end_time|std_flag"

        Returns:
            CallInfo: An instance of CallInfo with parsed attributes.

        Raises:
            ValueError: If the record does not contain exactly 5 fields.
        """
        parts = [part.strip() for part in record.split(RECORD_SEPARATOR) if part.strip()]
        if len(parts) != 5:
            raise ValueError("Record must contain exactly 5 fields")

        calling_number, receiving_number, start_time_str, end_time_str, is_std_call_str = parts
        start_time = datetime.strptime(start_time_str, DATETIME_FORMAT)
        end_time = datetime.strptime(end_time_str, DATETIME_FORMAT)
        is_std_call = int(is_std_call_str) == 1

        return cls(calling_number, receiving_number, start_time, end_time, is_std_call)

    def duration(self) -> int:
        """
        Calculates the duration of the call in seconds.

        Returns:
            int: Duration of the call in seconds.
        """
        return int((self.end_time - self.start_time).total_seconds())

# pylint: disable=abstract-method
class CallDurationFilter(MRJob):
    """
    MapReduce job to identify subscribers making high-duration STD calls.

    This job processes telecom call records to find phone numbers making more than
    60 minutes of STD (long distance) calls. This enables the telecom company to
    offer targeted STD packages to heavy users.

    Input Format:
        - Multiple text files containing call records
        - Each line: FromPhoneNumber|ToPhoneNumber|CallStartTime|CallEndTime|STDFlag
        - STDFlag: 1 for STD calls, 0 for local calls
        - DateTime format: YYYY-MM-DD HH:MM:SS

    Output Format:
        - Key-value pairs: (phone_number, total_std_duration_minutes)
        - Only includes phones with >60 minutes total STD call time
        - Tab-separated output format

    Example:
        Input:
            "9665128505|8983006310|2015-03-01 07:08:10|2015-03-01 08:12:15|1"
        
        Output:
            "9665128505\t64"  # 64 minutes of STD calls
    """
    INPUT_PROTOCOL = RawValueProtocol
    INTERNAL_PROTOCOL = JSONProtocol
    OUTPUT_PROTOCOL = RawProtocol

    def mapper(self, key: None, value: str):
        """
        Extracts and emits STD call durations per calling phone number for long calls.

        Processes each input call record line, parses it into a CallInfo object,
        and checks if the call is an STD call.

        If the call duration exceeds the defined minimum threshold,
        yields a tuple containing the calling phone number and the call duration in minutes.

        Args:
            key (None): Input key, ignored in processing.
            value (str): A line of call record data.

        Yields:
            tuple:
                (calling_number, duration_minutes) for STD calls
                exceeding the minimum duration threshold.
        """
        line = value.strip()
        call_info: CallInfo
        try:
            call_info = CallInfo.from_string(line)
            if call_info.is_std_call:
                call_duration = call_info.duration()
                if call_duration > MINIMUM_LONG_CALL_DURATION:
                    yield (
                        call_info.calling_number,
                        int(call_duration / SECONDS_IN_MINUTE)  # Convert to minutes
                    )
        except ValueError as _:
            # If the record is malformed or does not parse correctly, ignore it
            pass

    def combiner(self, key: str, values: Iterable[int]):
        """
        Aggregates call durations for a given phone number within a single mapper.

        This method reduces data transfer between the map and reduce phases by combining
        call durations locally. For each phone number, it yields the maximum call duration
        from the provided iterable of durations.

        Args:
            key (str): The phone number making STD calls.
            values (Iterable[int]):
                An iterable of call durations (in minutes) for this phone number.

        Yields:
            tuple:
                A tuple containing the phone number and the maximum call duration
                (in minutes) for this mapper.
        """
        yield key, max(values)

    def reducer(self, key: str, values: Iterable[int]):
        """
        Aggregates call durations for each unique calling number and yields the maximum duration.

        Args:
            key (str): The unique identifier for the calling number.
            values (Iterable[int]):
                An iterable of call durations associated with the calling number.

        Yields:
            out (tuple[str, str]):
                A tuple containing the calling number and its maximum call duration as strings.
        """
        yield str(key), str(max(values))

if __name__ == "__main__":
    CallDurationFilter.run()
