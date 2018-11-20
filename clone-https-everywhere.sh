#!/bin/bash
# Ensure we clone HTTPS Everywhere to a point where we have related histories
# for both the `release` branch and the `master` branch.

if [ "$#" != "3" ]; then
  echo "Usage: $0 REPO_LOCATION STABLE_BRANCH RELEASE_BRANCH"
fi

git clone --depth=10 --single-branch -b $3 $1
cd https-everywhere
git checkout -b $2

DEPTH=10

while ! git pull --depth=$DEPTH origin $2; do
  DEPTH=${DEPTH}0
done
