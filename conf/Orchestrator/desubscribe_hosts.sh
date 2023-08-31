#!/usr/bin/env bash

scriptDir=$(dirname -- "$(readlink -f -- "$BASH_SOURCE")")
source ${scriptDir}/../../set_pythonpath.sh
export ORCHESTRATOR_PATH=${SERVERLESS_PATH}/scripts/orchestrator
export LAYOUT_FILE=${scriptDir}/../layout.json

hosts=($(jq -r '.hosts[].name' ${LAYOUT_FILE}))
for name in "${hosts[@]}"
do
    echo "Desubscribing host: $name"
    bash $ORCHESTRATOR_PATH/Structures/desubscribe_host.sh ${name}
done