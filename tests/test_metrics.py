"""Unit tests for the metrics module."""

import json
import unittest
from pathlib import Path

from shinto.metrics import inc_persistant_counter, init_persistant_metrics, push_metric

APPLICATION_NAME = "my_app"
METRIC_PATH = Path("/tmp") # noqa: S108
METRIC_NAME = "request"


class TestMetrics(unittest.TestCase):
    """Test the metrics module."""

    def test_push_metric(self):
        """Test pushing a metric with default collector path."""
        push_metric(APPLICATION_NAME, METRIC_NAME, 100, METRIC_PATH)

        metric_file_path = Path(METRIC_PATH) / f"{APPLICATION_NAME}_{METRIC_NAME}.prom"
        self.assertTrue( Path(metric_file_path).exists() )

        with Path(metric_file_path).open("r") as f:
            data = f.read()
            self.assertIn(f"{APPLICATION_NAME}_{METRIC_NAME} = 100", data)


METRICS_FILE_NAME = Path("/tmp") / "metrics.json" # noqa: S108


class TestPersistantMetrics(unittest.TestCase):
    """Test the metrics module."""

    def tearDown(self):
        """Tear down the test."""
        Path(METRICS_FILE_NAME).unlink()

    def test_create_persistant_counter(self):
        """Test incrementing a persistent counter."""
        init_persistant_metrics(METRICS_FILE_NAME)

        self.assertEqual(inc_persistant_counter("my_app", "requests"), 1)
        self.assertEqual(inc_persistant_counter("my_app", "requests"), 2)

        with Path(METRICS_FILE_NAME).open("r") as f:
            data = json.load(f)
            counter_value = data.get("my_app_requests", 0)
            self.assertEqual(counter_value, 2)

    def test_inc_persistant_counter(self):
        """Test incrementing a persistent counter."""
        # Write a value to the metrics file (Simulating previous use)
        with Path(METRICS_FILE_NAME).open("w") as f:
            f.write('{"my_app_requests": 41}')

        init_persistant_metrics(METRICS_FILE_NAME)

        self.assertEqual(inc_persistant_counter("my_app", "requests"), 42)

        with Path(METRICS_FILE_NAME).open("r") as f:
            data = json.load(f)
            counter_value = data.get("my_app_requests", 0)
            self.assertEqual(counter_value, 42)


if __name__ == "__main__":
    unittest.main()
