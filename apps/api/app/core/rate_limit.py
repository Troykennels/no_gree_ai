"""Rate limiting (slowapi). A global per-IP default protects every endpoint;
sensitive routes (auth, simulate) add stricter per-route limits.

Storage is in-memory (fine for a single API instance / Railway single service).
For multiple replicas, point ``storage_uri`` at Redis so limits are shared.
"""

from __future__ import annotations

import os

from slowapi import Limiter
from slowapi.util import get_remote_address

_storage_uri = os.getenv("RATELIMIT_STORAGE_URI")  # e.g. redis://... in production

limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["240/minute"],
    storage_uri=_storage_uri or "memory://",
    # headers_enabled must stay False: our routes return Pydantic models, not raw
    # Response objects, and slowapi's header injection requires a Response.
    headers_enabled=False,
)
