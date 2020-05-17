# bids-schema

Perspective repository to contain (including historical) versions of BIDS
schema.  ATM this is just a place holder to eastablish necessary
scripting/workflows.  This repository would become ultimate source for schema,
including its released versions which would correspond to the versions of BIDS
specification where they come from.  It could be used as a git submodule  in
the repositories of tools which need to use it, or incorporated into their tree
(fully or partially) via `git subtree` mechanism.

- original schema itself will reside within bids-specification repository to
  streamline introducing changes to it within BIDS specification itself

- on a regular basis (on CRON or triggered by changes in master branch of
  bids-specification)  this repository would use `git subtree` to
  "extract" current schema into this repository.

- suggestive layout (implemented now, but without any copy/release yet)

  - `LICENSE`
  - `README.md`
  - `versions/`
    - `x.y.z/` - subdirectories matching versions of schema in BIDS specification
    - `master/` - the state of schema in master branch of the BIDS specification 
      repository
  - `tools/`

# HOWTOs

## `git subtree`

See http://github.com/dandi/dandi-core and its README.md for an example
of similar (not fully automated yet though) subtree use.

# References

- [bids-specification #466](https://github.com/bids-standard/bids-specification/issues/466)
  the issue discussing establishing of schema for BIDS
