#!/usr/bin/env bash

scriptDir=$(dirname -- "$(readlink -f -- "$BASH_SOURCE")")
source ${scriptDir}/../../set_pythonpath.sh
export ORCHESTRATOR_PATH=${SERVERLESS_PATH}/scripts/orchestrator
export LAYOUT_FILE=${scriptDir}/../layout.json

jq -c '.users[]' ${LAYOUT_FILE} | while read u; do
    echo "Subscribing user: $(echo ${u} | jq -c '.name')"
    bash $ORCHESTRATOR_PATH/Users/subscribe_user.sh ${u}
done