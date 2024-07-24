"""metrics module."""

import json
import os
from pathlib import Path

DEFAULT_PROMETHEUS_COLLECTER_PATH = os.getenv(
    "PROMETHEUS_COLLECTER_PATH", Path("/var/lib") / "node_exporter" / "textfile_collector"
)
DEFAULT_PERSISTANT_METRIC_JSONFILE = os.getenv(
    "PERSISTANT_METRIC_JSONFILE", Path("/var/lib") / "shinto" / "metrics.json"
)


def push_metric(
    application_name: str,
    metric: str,
    value: int,
    prometheus_collecter_path: str=DEFAULT_PROMETHEUS_COLLECTER_PATH):
    """
    Push a metric to the Prometheus Pushgateway.

    Args:
        application_name (str): The name of the application.
        metric (str): The name of the metric.
        value (int): The value of the metric.
        prometheus_collecter_path (str): The path to where the Prometheus
            textcollector will read prom files.

    """
    metric_file_path = Path(prometheus_collecter_path) / f"{application_name}_{metric}.prom"

    with Path(metric_file_path).open("w") as metric_file:
        metric_file.write(f"{application_name}_{metric} = {value}\n")


def inc_persistant_counter(
        application_name: str,
        metric: str) -> int:
    """
    Push a persistant counter to the Prometheus Pushgateway.

    Args:
        application_name (str): The name of the application.
        metric (str): The name of the metric.

    """
    return _get_persistant_metrics().inc_metric(application_name, metric)


class PersistantMetrics:
    """Persistant metrics class."""

    def __init__(
            self,
            metric_file:str=DEFAULT_PERSISTANT_METRIC_JSONFILE):
        """Initialize the PersistantMetrics class."""
        self._metric_file = metric_file
        self._metrics = {}
        self._load_metrics()

    def _load_metrics(self):
        """Load metrics from file."""
        # First check if path exists
        Path( self._metric_file).parent.mkdir(parents=True, exist_ok=True)
        # Write to file
        if Path(self._metric_file).exists():
            with Path(self._metric_file).open("r") as metric_file:
                self._metrics = json.load(metric_file) or {}

    def _save_metrics(self):
        """Save metrics to file."""
        with Path(self._metric_file).open("w") as metric_file:
            json.dump(self._metrics, metric_file)

    def push_metric(
            self,
            application_name: str,
            metric: str,
            value: int = 0 ):
        """
        Push a metric to the Prometheus Pushgateway.

        Args:
            application_name (str): The name of the application.
            metric (str): The name of the metric.
            value (int): The value of the metric.

        """
        self._metrics[f"{application_name}_{metric}"] = value
        self._save_metrics()

    def inc_metric(
            self,
            application_name: str,
            metric: str) -> int:
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
            self._metrics[f"{application_name}_{metric}"] = 1

        self._save_metrics()
        return self._metrics[f"{application_name}_{metric}"]


_persistant_metrics = None


def init_persistant_metrics(
        metric_file: str = DEFAULT_PERSISTANT_METRIC_JSONFILE
    ) -> PersistantMetrics:
    """Initialize the persistant metrics."""
    global _persistant_metrics # pylint: disable=global-statement # noqa: PLW0603
    _persistant_metrics = PersistantMetrics(metric_file)
    return _persistant_metrics


def _get_persistant_metrics() -> PersistantMetrics:
    global _persistant_metrics # pylint: disable=global-statement # noqa: PLW0603
    if _persistant_metrics is None:
        _persistant_metrics = init_persistant_metrics()
    return _persistant_metrics
