#!/usr/bin/env bash
scriptDir=$(dirname -- "$(readlink -f -- "$BASH_SOURCE")")
source "${scriptDir}/../../../set_pythonpath.sh"
python3 ${SERVERLESS_PATH}/src/Orchestrator/Orchestrator.py #2> orchestrator.log