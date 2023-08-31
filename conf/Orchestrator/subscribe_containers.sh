#!/usr/bin/env bash

scriptDir=$(dirname -- "$(readlink -f -- "$BASH_SOURCE")")
source ${scriptDir}/../../set_pythonpath.sh
export ORCHESTRATOR_PATH=${SERVERLESS_PATH}/scripts/orchestrator
export LAYOUT_FILE=${scriptDir}/../layout.json

jq -c '.containers[]' ${LAYOUT_FILE} | while read c; do
    echo "Subscribing container: $(echo ${c} | jq -c '.name')"
    bash $ORCHESTRATOR_PATH/Structures/subscribe_container.sh ${c}
done
