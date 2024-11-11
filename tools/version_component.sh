#!/bin/bash
#
# Provide list of components to come up with version for.
# Found in https://github.com/bids-standard/bids-schema/issues/7#issuecomment-1209540571

set -eu

repo="$1"
shift

cd "$repo"
if [ -z "$@" ]; then
    # no components given -- just 
    comm=HEAD
else
    comm=$(git log -1 --pretty=format:%H "$@*")
fi

cver=$(git describe --match=v[0-9].*.* "$comm")
ver=$(git describe --match=v[0-9].*.*)


# clean versions without possible git commits

if [ "${cver%%-*}" == "${ver%%-*}" ]; then
    out_ver="$cver"
else
    out_ver="${ver%%-*}"
fi

# make it more "semver" with using build marker although should not be used for comparison
out_ver="${out_ver/-/+}"
out_ver="${out_ver/v/}"

echo "DEBUG: cver=$cver ver=$ver out_ver=$out_ver" >&2  # for debugging
echo "$out_ver"
