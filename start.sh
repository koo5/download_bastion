#!/usr/bin/env bash

_term() {
  echo "Caught SIGTERM signal!"
  kill -TERM "$child" 2>/dev/null
}
trap _term SIGTERM

set -xv
if $WATCHMEDO; then
  watchmedo auto-restart --debounce-interval 1 --interval $WATCHMEDO_INTERVAL -d .  --patterns="*.py;*.egg" --recursive  -- ./start2.sh  &
else
  ./start2.sh  &
fi
child=$!
wait "$child"
echo "end"





