"""Advertise one service over mDNS, then stay out of the way.

A whole container for ~60 lines, on purpose. `zeroconf` is
**LGPL-2.1-or-later**; isolating it here is what lets the services around
it assert — and have CI enforce — that they have no copyleft dependency at
all. That asymmetry is the entire design: this image holds one LGPL
library and no business logic, so nothing else needs an exception.

Needs host networking. mDNS is multicast on 224.0.0.251:5353 and Docker's
bridge network does not forward multicast out to the physical LAN.

No HTTP server and no readiness endpoint. The record is registered once and
then re-announced by `zeroconf`'s own background threads, so this process
has nothing to do but hold the registration open — exiting would withdraw
it.
"""

import logging
import threading

from mdns_advertiser.config import Settings
from mdns_advertiser.mdns import advertise

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
logger = logging.getLogger(__name__)


def main() -> None:
    settings = Settings()
    logger.info(
        "Advertising %s as %s on port %d",
        settings.service_type,
        settings.instance_name,
        settings.port,
    )
    advertise(
        service_type=settings.service_type,
        port=settings.port,
        instance_name=settings.instance_name,
        properties=settings.properties_dict(),
    )

    # `advertise` swallows every failure by design — discovery is a
    # convenience on top of whatever pairing flow sits behind it, never a
    # dependency of it. So this process stays up either way: exiting on a
    # failed advertisement would make Compose restart-loop a container
    # whose job is already best-effort, and the log line above is the
    # honest signal.
    threading.Event().wait()


if __name__ == "__main__":
    main()
