# Advertise a service over mDNS. Build context is this directory:
#
#   docker build -t mdns-advertiser:0.1.0 .
#
# ## Run it
#
#   docker run --network host \
#     -e DISCOVERY_SERVICE_TYPE=_myapp._tcp.local. \
#     -e DISCOVERY_PORT=8443 \
#     -e DISCOVERY_INSTANCE_NAME=myapp \
#     mdns-advertiser:0.1.0
#
# `--network host` is required, not a preference: mDNS is multicast on
# 224.0.0.251:5353 and Docker's bridge network does not forward multicast
# out to the physical LAN.
#
# ## Why this image exists at all
#
# `zeroconf` is LGPL-2.1-or-later. Running it here, in its own container
# and its own repository, keeps it out of every consuming service's
# dependency tree — so those can enforce "no copyleft" in CI instead of
# carrying an exception. See docs/licensing.md.
FROM python:3.13-slim

RUN apt-get update && apt-get install -y --no-install-recommends ca-certificates \
 && rm -rf /var/lib/apt/lists/*
RUN pip install --no-cache-dir uv

WORKDIR /app
# LICENSE is not optional here: `pyproject.toml` declares it via
# `license-files`, so the build fails outright without it rather than
# quietly producing a wheel with no notice.
COPY pyproject.toml README.md LICENSE ./
COPY src ./src
RUN uv pip install --system --no-cache .

# LGPL-2.1 asks for notice, the licence text, and that the user be able to
# replace the library. The first two are here; the third is satisfied by
# `zeroconf` being pure Python, present as source in site-packages.
RUN mkdir -p /usr/share/licenses \
 && python - <<'PY'
import pathlib, re
from importlib import metadata
target = pathlib.Path("/usr/share/licenses")
rows = []
for dist in metadata.distributions():
    name = dist.metadata.get("Name")
    if not name:
        continue
    rows.append((name, dist.version or "?", dist.metadata.get("License-Expression")
                 or dist.metadata.get("License") or "see classifiers"))
    for f in dist.files or []:
        base = pathlib.PurePosixPath(f.as_posix()).name
        if re.fullmatch(r"(LICEN[CS]E|COPYING|NOTICE)[.\w-]*", base, re.I):
            try:
                out = target / name / base
                out.parent.mkdir(parents=True, exist_ok=True)
                out.write_text(f.read_text())
            except Exception:
                pass
lines = ["# Third-party notices", "", "| Package | Version | Licence |", "|---|---|---|"]
lines += [f"| {n} | {v} | {str(l).splitlines()[0][:60]} |" for n, v, l in sorted(rows)]
lines += ["", "zeroconf is LGPL-2.1-or-later. Its source is in site-packages and may be",
          "replaced. The base OS is an unmodified Debian image under its own terms."]
(target / "NOTICES.md").write_text("\n".join(lines))
print(f"wrote notices for {len(rows)} distributions")
PY

ENTRYPOINT ["python", "-m", "mdns_advertiser.main"]
