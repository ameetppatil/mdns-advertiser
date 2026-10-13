# Licensing

## What is in here

| Component | Licence | Notes |
|---|---|---|
| this project's code | proprietary (Cromozo Ltd) | ~60 lines; uses zeroconf, is not derived from it |
| `zeroconf` | **LGPL-2.1-or-later** | the reason this repository exists |
| `pydantic-settings`, `pydantic` | MIT | |
| base image | Debian (`python:3.13-slim`) | unmodified, redistributed under its own terms |

The per-image inventory is generated at build time into
`/usr/share/licenses/NOTICES.md`, with each dependency's licence text
beside it. Not hand-maintained — a hand-maintained one is wrong within a
month.

## The LGPL obligations, and how each is met

LGPL-2.1 permits proprietary software to *use* the library. It asks for
three things, all satisfied here:

1. **Notice that the library is used and under what terms.** This file, the
   `README`, `pyproject.toml`'s comment on the dependency, and the
   generated `NOTICES.md` in the image.
2. **The licence text travels with the binary.** Written to
   `/usr/share/licenses/zeroconf/` during the build.
3. **The user can replace the library.** `zeroconf` is pure Python and
   ships as source in `site-packages`; replacing it is editing files in the
   image. No relinking step exists to obstruct.

## Why a container, not just a module

A module boundary does not change a dependency tree. A *container* boundary
does: the consuming service no longer installs `zeroconf`, so its tree has
no copyleft in it and a build gate can enforce that.

That is the whole argument. Without the split, every consumer needs a
documented LGPL exception in its licence policy, and an exception that
appears in several policies is one nobody reads.

## If you fork or vendor this

The code is proprietary, so a copy needs Cromozo's permission — but the
*arrangement* is the valuable part and it is free to copy: isolate the
copyleft dependency in its own container, keep the wrapper trivial, and let
everything around it assert and enforce "no copyleft".
