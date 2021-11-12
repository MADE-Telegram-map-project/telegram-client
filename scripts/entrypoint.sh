#!/bin/bash

set -eu

./wait-it-and-start.sh --host="$RABBIT_MQ_HOST" --port="$RABBIT_MQ_PORT" -t ${TIMEOUT:-30}

exec "$@"