"""Unit tests for the metrics module."""

import json
import os
import unittest

from shinto.metrics import inc_persistant_counter, init_persistant_metrics, push_metric

APPLICATION_NAME = "my_app"
METRIC_PATH = "/tmp"
METRIC_NAME = "request"


class TestMetrics(unittest.TestCase):
    """Test the metrics module."""

    def tearDown(self):
        """Tear down the test."""
        # try:
        #     os.remove(os.path.join(METRIC_PATH, f"{APPLICATION_NAME}_{METRIC_NAME}.prom"))
        # except: # pylint: disable=broad-except # noqa: E722
        pass

    def test_push_metric(self):
        """Test pushing a metric with default collector path."""
        push_metric(APPLICATION_NAME, METRIC_NAME, 100, METRIC_PATH)

        metric_file_path = os.path.join(METRIC_PATH, f"{APPLICATION_NAME}_{METRIC_NAME}.prom")
        self.assertTrue(os.path.exists(metric_file_path))

        with open(metric_file_path, "r") as f:
            data = f.read()
            self.assertIn(f"{APPLICATION_NAME}_{METRIC_NAME} = 100", data)


METRICS_FILE_NAME = "/tmp/metrics.json"


class TestPersistantMetrics(unittest.TestCase):
    """Test the metrics module."""

    def tearDown(self):
        """Tear down the test."""
        try:
            os.remove(METRICS_FILE_NAME)
        except:  # pylint: disable=broad-except # noqa: E722
            pass

    def test_create_persistant_counter(self):
        """Test incrementing a persistent counter."""
        init_persistant_metrics(METRICS_FILE_NAME)

        self.assertEqual(inc_persistant_counter("my_app", "requests"), 1)
        self.assertEqual(inc_persistant_counter("my_app", "requests"), 2)

        with open(METRICS_FILE_NAME, "r") as f:
            data = json.load(f)
            counter_value = data.get("my_app_requests", 0)
            self.assertEqual(counter_value, 2)

    def test_inc_persistant_counter(self):
        """Test incrementing a persistent counter."""
        # Write a value to the metrics file (Simulating previous use)
        with open(METRICS_FILE_NAME, "w") as f:
            f.write('{"my_app_requests": 41}')

        init_persistant_metrics(METRICS_FILE_NAME)

        self.assertEqual(inc_persistant_counter("my_app", "requests"), 42)

        with open(METRICS_FILE_NAME, "r") as f:
            data = json.load(f)
            counter_value = data.get("my_app_requests", 0)
            self.assertEqual(counter_value, 42)


if __name__ == "__main__":
    unittest.main()
