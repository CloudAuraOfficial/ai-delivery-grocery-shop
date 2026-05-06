"""Secret resolution via Azure Key Vault (with Managed Identity), env fallback.

When AZURE_KEY_VAULT_URI is set, secrets are read from the named vault using
DefaultAzureCredential — which picks up Managed Identity automatically when
the workload runs on Azure (Container Apps, AKS, App Service, ACI). Locally
or on the VPS it falls back to the matching env var.

Secrets are cached in-process for the lifetime of the worker so each one
costs at most one vault round-trip per process.
"""

from __future__ import annotations

import os
import threading
from typing import Optional

import structlog

logger = structlog.get_logger()

_cache: dict[str, str] = {}
_lock = threading.Lock()
_client = None


def _kv_client():
    """Lazy-import azure SDKs only when a vault URI is configured."""
    global _client
    if _client is not None:
        return _client
    vault_uri = os.environ.get("AZURE_KEY_VAULT_URI")
    if not vault_uri:
        return None
    try:
        from azure.identity import DefaultAzureCredential
        from azure.keyvault.secrets import SecretClient
    except ImportError:
        logger.warning("kv_sdk_missing", hint="pip install azure-identity azure-keyvault-secrets")
        return None
    _client = SecretClient(vault_url=vault_uri, credential=DefaultAzureCredential())
    logger.info("kv_initialized", vault=vault_uri)
    return _client


def get(env_name: str, vault_secret_name: Optional[str] = None) -> str:
    """Resolve a secret. Vault if AZURE_KEY_VAULT_URI is set, env otherwise.

    vault_secret_name defaults to env_name lowercased with underscores → hyphens
    (Azure Key Vault naming convention).
    """
    if env_name in _cache:
        return _cache[env_name]

    with _lock:
        if env_name in _cache:
            return _cache[env_name]

        client = _kv_client()
        value = ""
        if client is not None:
            kv_name = vault_secret_name or env_name.lower().replace("_", "-")
            try:
                value = client.get_secret(kv_name).value or ""
                logger.info("kv_resolved", env=env_name, vault_secret=kv_name)
            except Exception as exc:
                logger.warning("kv_lookup_failed", env=env_name, error=str(exc))

        if not value:
            value = os.environ.get(env_name, "")

        _cache[env_name] = value
        return value
