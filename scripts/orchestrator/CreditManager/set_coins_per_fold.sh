#!/usr/bin/env bash
scriptDir=$(dirname -- "$(readlink -f -- "$BASH_SOURCE")")
source "${scriptDir}/../set_env.sh"

if [ -z "$1" ]
then
      echo "1 argument is needed"
      echo "1 -> amount for coins per fold (e.g., 0.1)"
      exit 1
fi

curl -X PUT -H "Content-Type: application/json" http://${ORCHESTRATOR_REST_URL}/service/credit_manager/COINS_PER_FOLD -d '{"value": "'$1'"}'
