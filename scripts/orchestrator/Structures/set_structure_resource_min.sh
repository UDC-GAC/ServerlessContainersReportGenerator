#!/usr/bin/env bash
scriptDir=$(dirname -- "$(readlink -f -- "$BASH_SOURCE")")
source "${scriptDir}/../set_env.sh"

if [ -z "$3" ]
then
      echo "3 arguments are needed"
      echo "1 -> structure name (e.g., node3, app1)"
      echo "2 -> resource name (e.g., cpu)"
      echo "3 -> resource value (e.g., 100)"
      exit 1
fi
curl -X PUT -H "Content-Type: application/json" http://${ORCHESTRATOR_REST_URL}/structure/$1/resources/$2/min -d '{"value":"'$3'"}'
