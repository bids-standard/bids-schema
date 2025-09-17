# bids-schema

Prospective repository of BIDS schema versions (including historical versions), as would
be required by validators supporting multiple versions.

At the moment this is just a pilot resource, as schema syntax and validator capabilities
are rapidly evolving. Eventually, this repository should become the authoritative BIDS
schema resource, including all released versions. It could be used as a git submodule
in the repositories of tools which need to use it, incorporated into their tree
(fully or partially) via the `git subtree` mechanism, or distributed separately by
package managers.

- The live BIDS schema, as used for all development work, will continue to reside within
  the `bids-specification` repository in order to streamline the addition and testing of
  changes.

- On a regular basis (via `cron` or push notifications from the `bids-specification`
  master branch) this repository should use e.g. `git subtree` to extract the current
  schema version and add it to its index.

- Proposed layout (implemented now, but without any copy/release yet):

  - `LICENSE`
  - `README.md`
  - `versions/`
    - `x.y.z/` - subdirectories matching schema versions in the BIDS specification
    - `latest/` - a copy (symlinks aren't supported on some operating systems) of the most recent release
    - `master/` - the state of schema in the BIDS specification master branch
      repository
  - `tools/`

# HOWTOs

## `git subtree`

See http://github.com/dandi/dandi-core and its README.md for an example of similar (not
yet fully automated) subtree use.

# References

- [bids-specification #466](https://github.com/bids-standard/bids-specification/issues/466)
  the issue discussing establishing of schema for BIDS

# Major TODOs

- Add rendering of PRs and BEPs
