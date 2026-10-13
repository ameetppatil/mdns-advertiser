import logging
import socket
import time

from zeroconf import ServiceInfo, Zeroconf

logger = logging.getLogger(__name__)

# NO DEFAULT, deliberately. The service type is the thing a client browses
# for, so a wrong one does not fail — it advertises into the void and looks
# exactly like "mDNS is broken on this network". Callers must say it.
#
# For reference, the appliance that this was extracted from browses for
# "_vonzl-gateway._tcp.local." as a constant compiled into its desktop
# client, with a test pinning the string. Shipped installs cannot be
# changed, so for that deployment the value is not negotiable.

_zeroconf: Zeroconf | None = None


def _local_ip(*, retries: int = 5, delay_seconds: float = 1.0) -> str:
    """The container's outbound-facing LAN IP, found the same way any
    "what's my local address" trick works: open a UDP socket "connected"
    to some public address (no packet is actually sent — UDP `connect`
    just picks a route) and read back the local endpoint it bound to.

    Retries with a short delay rather than failing straight away: right
    after this container starts (e.g. following a full DGX reboot), the
    host's network route to the outside world can take a few seconds to
    come up, so the very first attempt failing here is a transient
    startup race, not a real "this box has no network" condition — and
    getting it wrong is worse than it sounds, because whatever this
    returns gets baked into the mDNS advertisement for the rest of this
    process's life (`advertise()` below registers it once and only
    re-announces the same cached value). Raises (rather than ever
    returning something wrong like `127.0.0.1`) if every attempt fails —
    `advertise()`'s own `except Exception` already treats "couldn't
    determine an address" as an expected degraded mode and skips
    advertising entirely, which is the correct fallback: no
    advertisement at all (the manual "enter its address" path in
    Settings still works) is strictly better than confidently
    broadcasting an address that isn't this appliance's."""
    last_error: OSError | None = None
    for attempt in range(retries):
        if attempt:
            time.sleep(delay_seconds)
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            s.connect(("8.8.8.8", 80))
            return s.getsockname()[0]
        except OSError as e:
            last_error = e
        finally:
            s.close()
    assert last_error is not None
    raise last_error


def advertise(
    service_type: str,
    port: int,
    instance_name: str,
    properties: dict[str, str] | None = None,
) -> None:
    """Advertise a service on the LAN via mDNS/DNS-SD so a client's
    discovery picker can
    find it. This only ever populates that picker — a rogue device on the
    LAN that overhears the broadcast still can't do anything without also
    knowing the pairing code from this container's own logs, so discovery
    itself doesn't need to be authenticated.

    Deliberately swallows every exception here (name collisions —
    verified for real, two appliances defaulting to the same instance
    name on one LAN — missing multicast support, no usable network
    interface yet, ...): discovery is a convenience on top of pairing,
    never a dependency of it, and the manual "enter its address"
    fallback in Settings exists precisely for when mDNS doesn't work.
    Losing discovery must never take the appliance itself down; it just
    means an admin needs the manual-entry fallback instead."""
    global _zeroconf
    try:
        info = ServiceInfo(
            service_type,
            f"{instance_name}.{service_type}",
            # `server` is the SRV-record target — a normal "<name>.local."
            # hostname, deliberately distinct from the full service
            # instance name above. Left unset, `zeroconf` defaults it to
            # that instance name instead
            # (e.g. "myapp._myapp._tcp.local."), which
            # happens to still resolve on macOS (mDNSResponder answers
            # for whatever exact string this same process advertised)
            # but isn't a real hostname and isn't guaranteed to resolve
            # via avahi/nss-mdns on Linux or Bonjour-for-Windows — found
            # by inspecting a real paired `Firm.llm_endpoint_url` that
            # had captured that malformed value.
            server=f"{instance_name}.local.",
            addresses=[socket.inet_aton(_local_ip())],
            port=port,
            properties=properties or {},
        )
        _zeroconf = Zeroconf()
        _zeroconf.register_service(info)
        logger.info("Advertising %s on the LAN via mDNS", service_type)
    except Exception:
        logger.warning(
            "mDNS advertisement failed — the appliance is still fully usable via the "
            "manual 'enter its address' fallback in Settings, just not auto-discoverable.",
            exc_info=True,
        )
