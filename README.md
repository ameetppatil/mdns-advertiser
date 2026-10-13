# mdns-advertiser

Advertise a service on the LAN over mDNS/DNS-SD. One container, one job.

```sh
docker run --network host \
  -e DISCOVERY_SERVICE_TYPE=_myapp._tcp.local. \
  -e DISCOVERY_PORT=8443 \
  -e DISCOVERY_INSTANCE_NAME=myapp \
  mdns-advertiser:0.1.0
```

## Why this is its own repository

Not primarily for reuse — for **licence containment**.

`zeroconf` is **LGPL-2.1-or-later**. Any service that imports it has a
copyleft dependency in its tree, which means it cannot claim otherwise and
cannot have CI enforce otherwise. Moving mDNS behind a container boundary
and out into its own repository means every *consuming* service keeps a
dependency tree with no copyleft in it at all — a property a build gate can
check, rather than a claim someone re-verifies by hand.

So this image deliberately holds **one LGPL library and no business
logic**. That asymmetry is the design. It is ~60 lines so that nothing else
needs an exception.

Reusability is the side benefit, and it is real: nothing here knows what it
is advertising.

| Variable | Required | Notes |
|---|---|---|
| `DISCOVERY_SERVICE_TYPE` | **yes** | e.g. `_myapp._tcp.local.` — leading underscore and trailing dot both matter |
| `DISCOVERY_PORT` | **yes** | what clients will be told to connect to |
| `DISCOVERY_INSTANCE_NAME` | no (`appliance`) | also becomes the SRV target `<name>.local.` |
| `DISCOVERY_PROPERTIES` | no | TXT record, as `key=value,key=value` |

**`DISCOVERY_SERVICE_TYPE` has no default on purpose.** A wrong service
type does not error — it advertises into the void, which from the outside
is indistinguishable from "mDNS is broken on this network". An explicit
startup failure costs a minute; the silent version costs an afternoon.

## Host networking is required

mDNS is multicast on `224.0.0.251:5353`, and Docker's bridge network does
not forward multicast out to the physical LAN. `--network host` (or
`network_mode: host`) is not a preference.

## It never takes the caller down

`advertise()` swallows every failure — name collisions (seen for real, two
appliances defaulting to the same instance name on one LAN), missing
multicast support, no usable interface yet. Discovery is a convenience on
top of whatever pairing flow sits behind it, never a dependency of it, so
losing it must degrade to "enter the address manually" rather than to an
outage. The process stays up after a failed advertisement: restart-looping
a best-effort container hides the log line that explains it.

## Development

```sh
uv sync && uv run pytest    # no network, no container needed
docker build -t mdns-advertiser:0.1.0 .
```

## Licence

This project's own code is proprietary (Cromozo Ltd). It *uses* LGPL-2.1
`zeroconf` without being a derivative work of it, which the LGPL expressly
permits — see `docs/licensing.md` for how each obligation is met. It is
trivial enough to open-source if that is ever useful; nothing here depends
on it staying closed.
