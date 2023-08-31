#!/usr/bin/env bash

scriptDir=$(dirname -- "$(readlink -f -- "$BASH_SOURCE")")
source ${scriptDir}/../../set_pythonpath.sh
export ORCHESTRATOR_PATH=${SERVERLESS_PATH}/scripts/orchestrator
export LAYOUT_FILE=${scriptDir}/../layout.json

users=($(jq -r '.users[].name' ${LAYOUT_FILE}))
for name in "${users[@]}"
do
    echo "Desubscribing user: $name"
    bash $ORCHESTRATOR_PATH/Users/desubscribe_user.sh ${name}
done
