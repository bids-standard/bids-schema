"""Rendering: turn on-disk metadata into ``PRs/README.md`` and ``BEPs/README.md``.

Rendering is a pure function of on-disk state. It performs no HTTP calls
and no git operations. See ``bids_schema.collect`` for the collectors that
populate that state.
"""
