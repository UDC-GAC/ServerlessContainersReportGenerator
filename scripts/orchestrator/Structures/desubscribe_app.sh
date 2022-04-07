#!/usr/bin/env bash
scriptDir=$(dirname -- "$(readlink -f -- "$BASH_SOURCE")")
source "${scriptDir}/../set_env.sh"

if [ -z "$1" ]
then
      echo "1 argument is needed"
      echo "1 -> app name (e.g., app1)"
      exit 1
fi

curl -X DELETE -H "Content-Type: application/json" http://${ORCHESTRATOR_REST_URL}/structure/apps/$1
