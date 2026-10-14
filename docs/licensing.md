# Licensing

## What is in here

| Component | Licence | Notes |
|---|---|---|
| this project's code | **LGPL-2.1-or-later** | ~60 lines; same terms as the library it wraps |
| `zeroconf` | **LGPL-2.1-or-later** | the reason this repository exists |
| `pydantic-settings`, `pydantic` | MIT | |
| base image | Debian (`python:3.13-slim`) | unmodified, redistributed under its own terms |

The per-image inventory is generated at build time into
`/usr/share/licenses/NOTICES.md`, with each dependency's licence text
beside it. Not hand-maintained — a hand-maintained one is wrong within a
month.

## Why this project is LGPL too

It wraps `zeroconf`, which is LGPL-2.1-or-later. LGPL would have permitted a
proprietary wrapper — the library's whole purpose is to allow that — and
this project was originally written that way.

Licensing the wrapper under the **same terms** is simpler, and the
simplification is the point:

- **There is no derivative-work question left to argue.** A proprietary
  wrapper has to make the case that it merely *uses* the library rather than
  deriving from it. That case was sound, but it was a case. Under matching
  terms the question dissolves: the answer is yes, and it costs nothing.
- **No version-compatibility question either.** Matching `LGPL-2.1-or-later`
  exactly means there is no "can these two combine?" analysis at all.
- **It reads as what it is.** A generic mDNS advertiser, reusable by anyone,
  not a company asset that happens to live in its own repository.

## The LGPL obligations, and how each is met

They now apply to this project's own code as well as to `zeroconf`, and all
three are satisfied the same way:

1. **Notice that the library is used and under what terms.** This file, the
   `README`, `pyproject.toml`'s comment on the dependency, and the generated
   `NOTICES.md` in the image.
2. **The licence text travels with the binary.** `LICENSE` is copied into
   the image and installed as package metadata; `zeroconf`'s own text is
   written to `/usr/share/licenses/zeroconf/` during the build.
3. **The user can replace the library.** Both this code and `zeroconf` are
   pure Python and ship as source in `site-packages`; replacing either is
   editing files in the image. No relinking step exists to obstruct.

## Why a container, not just a module — and why that still holds

**This is the load-bearing part, and the licence change does not touch it.**

A module boundary does not change a dependency tree. A *container* boundary
does: the consuming service no longer installs `zeroconf`, so its tree has
no copyleft in it and a build gate can enforce that.

What protects a consumer is therefore **the process boundary, not this
project's licence**. The advertiser runs as its own container and is reached
over the network; it is a separate program, not a linked library, so neither
its code nor `zeroconf`'s reaches into anything that talks to it. That was
true when this wrapper was proprietary and it is equally true now.

Without the split, every consumer needs a documented LGPL exception in its
licence policy, and an exception that appears in several policies is one
nobody reads.

## If you fork or vendor this

Go ahead — it is LGPL-2.1-or-later, so you already have permission; keep the
licence and the notices with it.

The *arrangement* is the more valuable part, and that was always free to
copy: isolate the copyleft dependency in its own container, keep the wrapper
trivial, and let everything around it assert and enforce "no copyleft".
