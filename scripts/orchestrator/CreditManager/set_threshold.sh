#!/usr/bin/env bash
scriptDir=$(dirname -- "$(readlink -f -- "$BASH_SOURCE")")
source "${scriptDir}/../set_env.sh"

if [ -z "$1" ]
then
      echo "1 argument is needed"
      echo "1 -> amount for acum threshold (e.g., 60)"
      exit 1
fi

curl -X PUT -H "Content-Type: application/json" http://${ORCHESTRATOR_REST_URL}/service/credit_manager/ACUM_THRESHOLDS -d '{"value": "'$1'"}'
