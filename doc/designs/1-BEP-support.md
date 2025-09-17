ATM we have script @tools/inject-schema-fully-auto which clones bids-specification repository and then calls @tools/inject-schema for recently released versions of schema and also for the master branch.

The goal: we need to include building of schemas which are provided in PRs. Typically those are for BEPs, but not necessarily.  We would like to automate @tools/inject-schema-fully-auto so it also gives us schemas for relevant PRs and BEPs.

The approach

- goes through the list of PRs against bids-specification
  - this could be done if we fetch all the pull request references:

     git config --add remote.origin.fetch '+refs/pull/*:refs/pull/origin/*' && git fetch origin

  - and then go through them (the '.git/refs/pull/origin/*/merge' refs) and if any of them modifies src/schema:

    so that there is output for the diff -- must have changed schema... here is prototype loop


    for ref in .git/refs/pull/origin/*/merge; do git diff --stat origin/master...${ref#.git/} -- src/schema | grep . && echo "$ref HAS HIT" || echo "$ref -- nothing"; done

  - if there are changes for the schema: we prepare schema.json for that pr under PRs/${pr_number} folder.

  - if PR was merged, we can remove PRs/${pr} folder

  - if PR has no longer changes to schema, we also remove such folder

  - we commit changes with informative commit message per PR

- BEPs

  - in addition, we will clone https://github.com/bids-standard/bids-website/ which has "data/beps/beps.yml" which contains records like

```
  - number: '011'
    title: Structural preprocessing derivatives
    google_doc: https://docs.google.com/document/d/1YG2g4UkEio4t_STIBOqYOwneLEs1emHIXbGKynx7V0Y/
    pull_request: https://github.com/bids-standard/bids-specification/pull/518
    html_preview: https://bids-specification--518.org.readthedocs.build/en/518/05-derivatives/04-structural-derivatives.html
```

so if there is a pull_request field, then for that BEP we `cp -rp PRs/${pr}` (here 518) under `BEPs/${bep_number}` (here 011)

  - we do remove folder for BEP if there is no longer PRs/${pr_number}
  - we commit changes per each BEP


For that we also need to adjust and potentially rewrite tools/inject-schema so
it could take not just release identifier, but also handle an arbitrary git
ref, like in our case would be a ref to a PR.
