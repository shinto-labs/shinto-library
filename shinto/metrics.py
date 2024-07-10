# This file contains the PersistentCounter class which is a wrapper around the prometheus_client.Counter class.
# The PersistentCounter class is used to create a counter metric that persists its value to a file.

import os
import sys
from prometheus_client import Counter


DEFAULT_METRICS_FILE_PATH = os.path.join(sys.prefix, "lib", "shinto", "metrics")

class PersistentCounter:
    def __init__(self, name, help, filename = None):
        self.counter = Counter(name, help)
       
        if filename is None:
            filename = os.path.join(DEFAULT_METRICS_FILE_PATH, f"{name}.counter")
        self.filename = filename
       
        self.load_counter_value()

    def load_counter_value(self):
        if os.path.exists(self.filename):
            with open(self.filename, 'r') as file:
                value = float(file.read())
                self.counter._value.set(value)

    def increment(self):
        self.counter.inc()
        self.save_counter_value()

    def save_counter_value(self):
        if not os.path.exists(os.path.dirname(self.filename)):
            os.makedirs(os.path.dirname(self.filename))

        with open(self.filename, 'w') as file:
            file.write(str(self.counter._value.get()))
