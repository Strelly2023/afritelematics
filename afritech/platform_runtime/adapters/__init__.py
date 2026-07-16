"""Operational adapters for NovaTech runtime execution."""

from .base import AdapterExecutionMode, OperationalAdapter, ResourceDiscovery
from .docker_compose import DockerComposeDeploymentAdapter
from .kubernetes import KubernetesDeploymentAdapter
from .nats import NatsJetStreamAdapter
from .object_storage import S3ObjectStorageAdapter
from .postgres import PostgresProvisioningAdapter
from .redis import RedisAdapter
from .secrets import SecretManagerAdapter
from .systemd import SystemdDeploymentAdapter
from .workers import DockerComposeWorkerAdapter, KubernetesWorkerAdapter, LocalProcessWorkerAdapter, WorkerProcessSpec

__all__ = [
    "AdapterExecutionMode",
    "DockerComposeDeploymentAdapter",
    "DockerComposeWorkerAdapter",
    "KubernetesDeploymentAdapter",
    "KubernetesWorkerAdapter",
    "LocalProcessWorkerAdapter",
    "NatsJetStreamAdapter",
    "OperationalAdapter",
    "RedisAdapter",
    "ResourceDiscovery",
    "S3ObjectStorageAdapter",
    "SecretManagerAdapter",
    "SystemdDeploymentAdapter",
    "PostgresProvisioningAdapter",
    "WorkerProcessSpec",
]
