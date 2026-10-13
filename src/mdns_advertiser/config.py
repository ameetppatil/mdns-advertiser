from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Env-configured, `DISCOVERY_` prefix.

    `service_type` has **no default**, so the container refuses to start
    without one. That is the right failure: advertising the wrong service
    type does not error, it advertises into the void, and from the outside
    that is indistinguishable from "mDNS does not work on this network".
    An explicit startup failure costs a minute; the silent version costs an
    afternoon.
    """

    model_config = SettingsConfigDict(env_prefix="DISCOVERY_", extra="ignore")

    # e.g. "_myapp._tcp.local." — note the leading underscore and the
    # trailing dot; DNS-SD is strict about both.
    service_type: str

    # Must match whatever actually listens. This service advertises a
    # record; it does not check that anything is behind it.
    port: int
    instance_name: str = "appliance"

    # Optional TXT record contents, as `key=value,key=value`. Clients that
    # version their discovery protocol use this.
    properties: str = ""

    def properties_dict(self) -> dict[str, str]:
        out: dict[str, str] = {}
        for pair in self.properties.split(","):
            if "=" in pair:
                k, v = pair.split("=", 1)
                out[k.strip()] = v.strip()
        return out
