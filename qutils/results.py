import os

from typing import List, Any
from abc import ABC, abstractmethod


class BaseParser(ABC):
    """
    An util class to parse logs, where each log file generate
    one record
    The results looks like:
        data0 data1 data2 ... dataN
        data0 data1 data2 ... dataN
           ...
        data0 data1 data2 ... dataN
    We assume that the first column is the record key, i.e., a string
    and the rest are float values
    """

    def __init__(self, logs_path, *args) -> None:
        self.logs_path = logs_path
        self.parse_args = args

        # Record each result returned by parse_one
        self.results = []

    def run(self):
        """Traverse given logs_path, parse and generate a record for each log"""
        avg = []
        cnt = 0
        for root, dirs, files in os.walk(self.logs_path):
            files.sort()
            for f in files:
                file_path = os.path.join(root, f)
                one_res = self.parse_one(file_path, *self.parse_args)
                if not one_res:
                    continue
                self.results.append(one_res)
                print("\t".join([str(it) for it in one_res]))
                cnt += 1
                if not avg:
                    avg = [0.0] * len(one_res[1:])
                for i in range(len(avg)):
                    avg[i] += one_res[i + 1]
        print("\t".join(["avg"] + [str(it / cnt) for it in avg]))

    @abstractmethod
    def parse_one(self, file_path, *args) -> List[Any]:
        pass
