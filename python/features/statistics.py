#!/usr/bin/env python3
import csv
import logging
import os
from datetime import datetime

STATS_FILENAME = 'tvb-stats.csv'


def _stats_path():
    data_dir = os.environ.get('TVB_DATA_DIR')
    return os.path.join(data_dir, STATS_FILENAME) if data_dir else STATS_FILENAME


class Filesize:
    chunk = 1024
    units = ['bytes', 'KB', 'MB', 'GB', 'TB', 'PB']
    precisions = [0, 0, 1, 2, 2, 2]

    def __init__(self, size):
        self.size = size

    def __int__(self):
        return self.size

    def __str__(self):
        if self.size == 0:
            return '0 bytes'
        from math import log
        unit = self.units[min(int(log(self.size, self.chunk)), len(self.units) - 1)]
        return self.format(unit)

    def format(self, unit):
        if unit not in self.units:
            raise Exception(f"Not a valid file size unit: {unit}")
        if self.size == 1 and unit == 'bytes':
            return '1 byte'
        exponent = self.units.index(unit)
        quotient = float(self.size) / self.chunk ** exponent
        precision = self.precisions[exponent]
        format_string = '{:.%sf} {}' % precision
        return format_string.format(quotient, unit)


def write_statistics(statistics_data):
    delimiter = ';'
    header = ['Encoded Date', 'Filename', 'Original Size', 'New Size',
              'Percentage', 'Duration of Encode', 'Command']

    stats_path = _stats_path()
    parent = os.path.dirname(stats_path)
    if parent:
        os.makedirs(parent, exist_ok=True)

    if os.path.exists(stats_path):
        mode = 'a'
    else:
        mode = 'w'

    with open(stats_path, mode, newline='', encoding='utf-8') as stats_file:
        writer = csv.writer(stats_file, delimiter=delimiter,
                           quotechar='"', quoting=csv.QUOTE_MINIMAL)
        if mode == 'w':
            writer.writerow(header)
        writer.writerow(statistics_data)

    logging.debug(f"Statistics written to {stats_path}")
