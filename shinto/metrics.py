"""metrics module."""

import os

DEFAULT_PROMETHEUS_COLLECTER_PATH="/var/lib/node_exporter/textfile_collector"


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
