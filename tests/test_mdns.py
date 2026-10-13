import socket

SERVICE_TYPE = "_myapp._tcp.local."

import pytest

from mdns_advertiser import mdns as discovery


@pytest.fixture
def fast_local_ip(monkeypatch):
    """`advertise()` tests below aren't exercising real network
    self-IP-detection — that's `test__local_ip_*`'s job further down —
    so stub it to something instant and deterministic."""
    monkeypatch.setattr(discovery, "_local_ip", lambda: "192.168.1.50")


def test_advertise_sets_a_real_hostname_distinct_from_the_service_instance_name(
    monkeypatch, fast_local_ip
):
    """Regression test: `server` must be an explicit, normal hostname —
    left unset, `zeroconf.ServiceInfo` defaults it to the full service
    instance name (e.g. "myapp._myapp._tcp.local."),
    which a real `Firm.llm_endpoint_url` was once captured with. That
    only happens to resolve on macOS; it's not a real hostname."""
    captured = {}

    class FakeServiceInfo:
        def __init__(self, type_, name, **kwargs):
            captured["type_"] = type_
            captured["name"] = name
            captured["server"] = kwargs.get("server")

    class FakeZeroconf:
        def register_service(self, info):
            captured["registered"] = info

    monkeypatch.setattr(discovery, "ServiceInfo", FakeServiceInfo)
    monkeypatch.setattr(discovery, "Zeroconf", FakeZeroconf)

    discovery.advertise(
        service_type=SERVICE_TYPE, port=8443, instance_name="myapp"
    )

    assert captured["server"] == "myapp.local."
    assert captured["server"] != captured["name"]


def test_advertise_never_raises_when_registration_fails(monkeypatch, fast_local_ip):
    """Regression test: a real name collision between two appliances on
    one LAN (both defaulting to the same instance name) raised
    `zeroconf._exceptions.NonUniqueNameException` straight out of
    `register_service` and crashed the whole gateway process before it
    ever reached `uvicorn.run()` — verified against a real second
    appliance. Discovery failing must never take pairing down with it."""

    class FakeZeroconfThatFails:
        def register_service(self, info):
            raise RuntimeError("simulated: name already in use on this LAN")

    monkeypatch.setattr(discovery, "Zeroconf", FakeZeroconfThatFails)

    discovery.advertise(
        service_type=SERVICE_TYPE, port=8443, instance_name="myapp"
    )  # must not raise


def test_advertise_never_raises_and_skips_registration_when_no_address_can_be_found(monkeypatch):
    """Regression test for a real production incident: right after a full
    reboot, the container's route to the outside world wasn't up yet the
    very first time `_local_ip` tried it, so the old code silently fell
    back to advertising `127.0.0.1` — and kept re-announcing that bogus
    address for the container's entire uptime, since it's only computed
    once. Every client on the LAN then resolved the appliance's hostname
    to their own loopback and failed. Advertising nothing at all (this
    test's expectation) is the correct degraded mode; advertising a
    wrong-but-plausible address is worse than that."""

    def always_fails():
        raise OSError("simulated: no route to 8.8.8.8 yet")

    monkeypatch.setattr(discovery, "_local_ip", always_fails)

    def fail_if_called(*args, **kwargs):
        raise AssertionError("must not attempt to register a service with no known address")

    monkeypatch.setattr(discovery, "ServiceInfo", fail_if_called)

    discovery.advertise(
        service_type=SERVICE_TYPE, port=8443, instance_name="myapp"
    )  # must not raise


class _RecordingSocket:
    """Stands in for `socket.socket` — `connect` fails a fixed number of
    times before succeeding, so `_local_ip`'s retry loop has something
    real to retry against without an actual network call."""

    remaining_failures = 0
    connect_attempts = 0

    def __init__(self, *args, **kwargs):
        pass

    def connect(self, address):
        _RecordingSocket.connect_attempts += 1
        if _RecordingSocket.remaining_failures > 0:
            _RecordingSocket.remaining_failures -= 1
            raise OSError("simulated: network not up yet")

    def getsockname(self):
        return ("192.168.1.50", 0)

    def close(self):
        pass


def test__local_ip_retries_a_transient_startup_failure_then_succeeds(monkeypatch):
    _RecordingSocket.remaining_failures = 2
    _RecordingSocket.connect_attempts = 0
    monkeypatch.setattr(socket, "socket", _RecordingSocket)

    ip = discovery._local_ip(retries=5, delay_seconds=0)

    assert ip == "192.168.1.50"
    assert _RecordingSocket.connect_attempts == 3


def test__local_ip_raises_once_every_retry_is_exhausted(monkeypatch):
    _RecordingSocket.remaining_failures = 99
    _RecordingSocket.connect_attempts = 0
    monkeypatch.setattr(socket, "socket", _RecordingSocket)

    with pytest.raises(OSError):
        discovery._local_ip(retries=3, delay_seconds=0)

    assert _RecordingSocket.connect_attempts == 3
