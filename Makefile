# mdns-advertiser — a container that holds one LGPL dependency so that
# nothing around it has to. See README.md and docs/licensing.md.
IMAGE ?= mdns-advertiser:0.1.0

.DEFAULT_GOAL := help

.PHONY: help
help:
	@echo "  make test     pytest (no container, no network)"
	@echo "  make build    docker build -t $(IMAGE)"
	@echo "  make run      run it against a throwaway service type"
	@echo "  make notices  print the generated third-party notices from the image"

.PHONY: test
test:
	@uv run pytest -q

.PHONY: build
build:
	@docker build -t $(IMAGE) .

# Host networking is required — mDNS is multicast and Docker's bridge does
# not forward it to the LAN.
.PHONY: run
run:
	@docker run --rm --network host \
	  -e DISCOVERY_SERVICE_TYPE=_mdns-advertiser-smoke._tcp.local. \
	  -e DISCOVERY_PORT=9999 \
	  -e DISCOVERY_INSTANCE_NAME=smoke \
	  $(IMAGE)

.PHONY: notices
notices:
	@docker run --rm --entrypoint cat $(IMAGE) /usr/share/licenses/NOTICES.md
