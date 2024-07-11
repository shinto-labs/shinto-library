"""metrics module."""

import json
import os

DEFAULT_PROMETHEUS_COLLECTER_PATH = os.getenv("PROMETHEUS_COLLECTER_PATH", "/var/lib/node_exporter/textfile_collector")
DEFAULT_PERSISTANT_METRIC_JSONFILE = os.getenv("PERSISTANT_METRIC_JSONFILE", "/var/lib/shinto/metrics.json")


def push_metric(
        application_name,
        metric,
        value,
        prometheus_collecter_path=DEFAULT_PROMETHEUS_COLLECTER_PATH ):
    """
    Push a metric to the Prometheus Pushgateway.

    Args:
        application_name (str): The name of the application.
        metric (str): The name of the metric.
        value (int): The value of the metric.
        prometheus_collecter_path (str): The path to where the Prometheus
            textcollector will read prom files.

    """
    metric_file_path = os.path.join(prometheus_collecter_path, f"{application_name}_{metric}.prom")

    with open(metric_file_path, "w") as metric_file:
        metric_file.write(f"{application_name}_{metric} = {value}\n")


def inc_persistant_counter(application_name, metric) -> int:
    """
    Push a persistant counter to the Prometheus Pushgateway.

    Args:
        application_name (str): The name of the application.
        metric (str): The name of the metric.

    """
    return _get_persistant_metrics().inc_metric(application_name, metric)


class PersistantMetrics:
    """Persistant metrics class."""

    _metrics: dict = {}
    _metrics_file: str = ""

    def __init__(self, metric_file=DEFAULT_PERSISTANT_METRIC_JSONFILE):
        """Initialize the PersistantMetrics class."""
        self._metric_file = metric_file
        self._metrics = {}
        self._load_metrics()

    def _load_metrics(self):
        """Load metrics from file."""
        # First check if path exists
        os.makedirs(os.path.dirname(self._metric_file), exist_ok=True)
        # Write to file
        if os.path.exists(self._metric_file):
            with open(self._metric_file, "r") as metric_file:
                self._metrics = json.load(metric_file) or {}

    def _save_metrics(self):
        """Save metrics to file."""
        with open(self._metric_file, "w") as metric_file:
            json.dump(self._metrics, metric_file)

    def push_metric(self, application_name, metric, value = 0):
        """
        Push a metric to the Prometheus Pushgateway.

        Args:
            application_name (str): The name of the application.
            metric (str): The name of the metric.
            value (int): The value of the metric.

        """
        self._metrics[f"{application_name}_{metric}"] = value
        push_metric(application_name, metric, value)
        self._save_metrics()

    def inc_metric(self, application_name, metric) -> int:
        """
        Increment a metric.

        Args:
            application_name (str): The name of the application.
            metric (str): The name of the metric.

        """
        if f"{application_name}_{metric}" in self._metrics:
            try:
                self._metrics[f"{application_name}_{metric}"] += 1
            except TypeError:
                self._metrics[f"{application_name}_{metric}"] = 1
        else:
            self._metrics[f"{application_name}_{metric}"] =  1

        self._save_metrics()
        push_metric(application_name, metric, self._metrics[f"{application_name}_{metric}"])
        return self._metrics[f"{application_name}_{metric}"]

_persistant_metrics = None

def init_persistant_metrics(metric_file=DEFAULT_PERSISTANT_METRIC_JSONFILE) -> PersistantMetrics:
    """Initialize the persistant metrics."""
    global _persistant_metrics
    _persistant_metrics = PersistantMetrics(metric_file)
    return _persistant_metrics

def _get_persistant_metrics() -> PersistantMetrics:
    global _persistant_metrics
    if _persistant_metrics is None:
        _persistant_metrics = init_persistant_metrics()
    return _persistant_metrics

