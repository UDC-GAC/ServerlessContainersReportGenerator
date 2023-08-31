#!/usr/bin/env bash

scriptDir=$(dirname -- "$(readlink -f -- "$BASH_SOURCE")")
source ${scriptDir}/../../set_pythonpath.sh
export ORCHESTRATOR_PATH=${SERVERLESS_PATH}/scripts/orchestrator
export LAYOUT_FILE=${scriptDir}/../layout.json

jq -c '.apps[]' ${LAYOUT_FILE} | while read a; do
    echo "Subscribing application: $(echo ${a} | jq -c '.name')"
    bash $ORCHESTRATOR_PATH/Structures/subscribe_app.sh ${a}
done