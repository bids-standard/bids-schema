"""``bids-schema`` CLI entry point.

Top-level ``click`` group with subcommands:

- ``bids-schema collect prs``  — fetch PR stats via GitHub GraphQL.
- ``bids-schema collect beps`` — walk ``bids-website:data/beps/beps.yml`` history.
- ``bids-schema render prs``   — write ``PRs/README.md`` from on-disk metadata.
- ``bids-schema render beps``  — write ``BEPs/README.md`` from on-disk metadata.
- ``bids-schema cycle``        — collect prs && collect beps && render prs && render beps.
- ``bids-schema info``         — dump versions and auth status (debugging).

Collection and rendering are always cleanly separable: rendering reads only
on-disk JSON, and collection never writes rendered output.
"""

from __future__ import annotations

import sys

import click

from bids_schema import __version__


@click.group(help="Tooling for the bids-schema archive.")
@click.version_option(__version__, prog_name="bids-schema")
def main() -> None:  # pragma: no cover - trivial dispatcher
    pass


@main.group(help="Collect data from external sources into on-disk metadata.")
def collect() -> None:  # pragma: no cover - trivial dispatcher
    pass


@main.group(help="Render Markdown READMEs from on-disk metadata.")
def render() -> None:  # pragma: no cover - trivial dispatcher
    pass


@collect.command("prs", help="Collect PR stats via GitHub GraphQL.")
@click.option("--all", "collect_all", is_flag=True, default=True,
              help="Collect all PRs currently on disk (default).")
@click.option("--only", "only", multiple=True, type=str,
              help="Restrict to specific PR numbers (repeatable).")
@click.option("--force", is_flag=True, help="Ignore freshness gate.")
def collect_prs(collect_all: bool, only: tuple[str, ...], force: bool) -> None:
    from bids_schema.collect import github

    only_list = list(only) if only else None
    exit_code = github.collect(only=only_list, force=force)
    sys.exit(exit_code)


@collect.command("beps", help="Collect BEP registration timestamps from bids-website git history.")
@click.option("--all", "collect_all", is_flag=True, default=True,
              help="Collect all BEPs currently on disk (default).")
@click.option("--only", "only", multiple=True, type=str,
              help="Restrict to specific BEP numbers (repeatable).")
@click.option("--force", is_flag=True, help="Ignore freshness gate.")
@click.option("--skip-fetch", is_flag=True,
              help="Don't run `git fetch` before walking history (for air-gapped debugging).")
def collect_beps(collect_all: bool, only: tuple[str, ...], force: bool, skip_fetch: bool) -> None:
    from bids_schema.collect import bep_registration

    only_list = list(only) if only else None
    exit_code = bep_registration.collect(only=only_list, force=force, skip_fetch=skip_fetch)
    sys.exit(exit_code)


@render.command("prs", help="Write PRs/README.md from on-disk metadata.")
def render_prs() -> None:
    from bids_schema.render import pr_readme

    pr_readme.render_to_disk()


@render.command("beps", help="Write BEPs/README.md from on-disk metadata.")
def render_beps() -> None:
    from bids_schema.render import bep_readme

    bep_readme.render_to_disk()


@main.command("cycle", help="Composite: collect prs && collect beps && render prs && render beps.")
def cycle() -> None:
    # Call the underlying implementations directly (not the click commands)
    # so a non-zero exit from one collector doesn't skip subsequent phases.
    from bids_schema.collect import bep_registration, github
    from bids_schema.render import bep_readme, pr_readme

    github.collect()
    bep_registration.collect()
    pr_readme.render_to_disk()
    bep_readme.render_to_disk()


@main.command("info", help="Print tool version, auth status, and other debug info.")
def info() -> None:
    import shutil
    import subprocess

    click.echo(f"bids-schema version: {__version__}")
    click.echo(f"python: {sys.version.split()[0]}")
    gh = shutil.which("gh")
    click.echo(f"gh CLI: {gh or 'not found on PATH'}")
    if gh:
        try:
            result = subprocess.run([gh, "auth", "status"], capture_output=True, text=True, check=False)
            for line in (result.stderr or result.stdout or "").splitlines():
                click.echo(f"  {line}")
        except OSError as e:  # pragma: no cover
            click.echo(f"  (gh auth status failed: {e})")


if __name__ == "__main__":  # pragma: no cover
    main()
