#!/bin/sh
# Run `./atlas.py` when the container is first started

if [ ! -f /tmp/atlas_first_run ]; then
  touch /tmp/atlas_first_run
  ./atlas.py
fi

$@
