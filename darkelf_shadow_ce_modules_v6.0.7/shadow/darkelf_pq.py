"""
darkelf_pq.py

Centralized Post-Quantum state manager for Darkelf Shadow.
Enhanced: thread-safe state transitions, bounded memory, and stricter lifecycle controls.
"""

from __future__ import annotations

import hashlib
import hmac
import secrets
import threading
import time
from collections import deque


def darkelf_pq_fingerprint(
    url: str, headers: dict | None = None, seed: bytes | None = None
) -> str:
    h = hashlib.sha3_512()
    h.update(url.encode("utf-8", errors="ignore"))

    if headers:
        for k, v in sorted(headers.items()):
            h.update(str(k).encode("utf-8", errors="ignore"))
            h.update(str(v).encode("utf-8", errors="ignore"))

    # 10s epoch bucket (keeps short-term churn while limiting long-term linkability)
    h.update(str(int(time.time() // 10)).encode("utf-8"))

    if seed:
        h.update(seed)

    return h.hexdigest()


def darkelf_pq_chain(seed: bytes, url: str, counter: int) -> bytes:
    h = hashlib.sha3_512()
    h.update(seed)
    h.update(url.encode("utf-8", errors="ignore"))
    h.update(counter.to_bytes(8, "big"))
    return h.digest()


def darkelf_pq_mix(url: str) -> str:
    nonce = secrets.token_hex(8)
    return hashlib.sha3_512((url + nonce + str(time.time())).encode("utf-8")).hexdigest()


def darkelf_hkdf_sha3(
    key: bytes,
    salt: bytes = b"darkelf",
    info: bytes = b"pq-layer",
) -> bytes:
    prk = hmac.new(salt, key, hashlib.sha3_512).digest()
    return hmac.new(prk, info, hashlib.sha3_512).digest()


class DarkelfPQ:
    """Central PQ state container."""

    MAX_SEEN = 5000
    TRIM_TO = 2500
    TAB_ID_BOOT = "boot"

    def __init__(self):
        self._lock = threading.RLock()
        self._destroyed = False

        self.tab_seeds: dict[str, bytes] = {}
        self.counters: dict[str, int] = {}
        self.canvas_seeds: dict[str, int] = {}
        self.seen: set[str] = set()
        self._seen_fifo: deque[str] = deque()  # preserves insertion order for accurate trimming

        self.chain: str | None = None
        self.generation = 0
        self.rekeys = 0
        self.total_requests = 0
        self.last_update = 0.0
        self.seed_created = 0.0

        self.initialize()

    def _ensure_alive(self):
        if self._destroyed:
            raise RuntimeError("DarkelfPQ has been destroyed")

    def initialize(self):
        with self._lock:
            self._destroyed = False

            seed = secrets.token_bytes(32)
            self.chain = hashlib.sha3_512(seed).hexdigest()

            self.counters[self.TAB_ID_BOOT] = 1
            self.tab_seeds[self.TAB_ID_BOOT] = seed
            self.canvas_seeds[self.TAB_ID_BOOT] = int.from_bytes(seed[:4], "big")

            now = time.time()
            self.seed_created = now
            self.last_update = now
            self.generation += 1

    def get_tab_seed(self, tab_id: str) -> bytes:
        with self._lock:
            self._ensure_alive()
            if tab_id not in self.tab_seeds:
                seed = secrets.token_bytes(32)
                self.tab_seeds[tab_id] = seed
                self.canvas_seeds[tab_id] = int.from_bytes(seed[:4], "big")
                self.counters[tab_id] = 0
            return self.tab_seeds[tab_id]

    def update_chain(self, tab_id: str, url: str):
        with self._lock:
            self._ensure_alive()
            seed = self.get_tab_seed(tab_id)
            counter = self.counters.get(tab_id, 0)

            self.chain = hashlib.sha3_512(
                seed + url.encode("utf-8", errors="ignore") + counter.to_bytes(8, "big")
            ).hexdigest()

            self.counters[tab_id] = counter + 1
            self.last_update = time.time()

    def canvas_seed(self, tab_id: str) -> int:
        with self._lock:
            self._ensure_alive()
            return self.canvas_seeds.get(tab_id, 0)

    def observe(self, url: str, request_type: str | None, seed: bytes):
        if request_type not in ("xmlhttprequest", "subdocument", "media"):
            return

        with self._lock:
            self._ensure_alive()
            if not self.chain:
                return

            fp = darkelf_pq_fingerprint(url, seed=seed)

            # Add only if truly new (maintain accurate FIFO mirror for trimming)
            if fp not in self.seen:
                self.seen.add(fp)
                self._seen_fifo.append(fp)

            self.total_requests += 1

            self.chain = hashlib.sha3_512(
                self.chain.encode("utf-8") + fp.encode("utf-8")
            ).hexdigest()
            self.last_update = time.time()

            if len(self.seen) > self.MAX_SEEN:
                target_remove = len(self.seen) - self.TRIM_TO
                for _ in range(max(0, target_remove)):
                    if not self._seen_fifo:
                        break
                    old = self._seen_fifo.popleft()
                    self.seen.discard(old)

    def status(self) -> str:
        with self._lock:
            self._ensure_alive()
            if sum(self.counters.values()) <= 1:
                return "standby"
            return "active"

    def seed_age(self) -> int:
        with self._lock:
            self._ensure_alive()
            return int(time.time() - self.seed_created)

    def derive_key(self, label: bytes) -> bytes:
        with self._lock:
            self._ensure_alive()
            if not isinstance(label, (bytes, bytearray)) or len(label) == 0:
                raise ValueError("label must be non-empty bytes")
            return darkelf_hkdf_sha3(
                self.get_tab_seed(self.TAB_ID_BOOT),
                info=bytes(label),
            )

    def status_info(self) -> dict:
        with self._lock:
            self._ensure_alive()
            return {
                "status": self.status(),
                "generation": self.generation,
                "rekeys": self.rekeys,
                "seed_age": int(time.time() - self.seed_created),
                "last_update": int(time.time() - self.last_update),
                "requests": self.total_requests,
                "tabs": len(self.tab_seeds),
                "observed": len(self.seen),
            }



    def watchdog(self) -> dict:
        """
        Lightweight runtime integrity check.
        Returns health information without mutating state unless recovery is required.
        """
        with self._lock:
            healthy = True
            issues = []

            if self._destroyed:
                healthy = False
                issues.append("destroyed")

            if self.chain is None:
                healthy = False
                issues.append("missing_chain")

            if self.generation <= 0:
                healthy = False
                issues.append("invalid_generation")

            if self.seed_created <= 0:
                healthy = False
                issues.append("missing_seed")

            if not healthy and not self._destroyed:
                # Recover from transient corruption by starting a fresh session.
                self.rekeys += 1
                self.initialize()
                issues.append("auto_reinitialized")

            return {
                "healthy": healthy,
                "issues": issues,
                "generation": self.generation,
                "status": self.status() if not self._destroyed else "destroyed",
            }
            
    def destroy(self):
        """
        Destroy all session-only Quantum state.

        This removes references to transient cryptographic state so it
        becomes eligible for garbage collection. No state is persisted.
        """
        with self._lock:
            self.tab_seeds.clear()
            self.canvas_seeds.clear()
            self.counters.clear()
            self.seen.clear()
            self._seen_fifo.clear()

            self.chain = None
            self.last_update = 0.0
            self.seed_created = 0.0
            self.total_requests = 0

            self._destroyed = True

    def reset(self):
        """
        Destroy existing state and begin a new Quantum session.
        """
        with self._lock:
            self.rekeys += 1
            self.destroy()
            self.initialize()
