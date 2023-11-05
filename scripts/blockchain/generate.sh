#!/usr/bin/env bash
scriptDir=$(dirname -- "$(readlink -f -- "$BASH_SOURCE")")

export REPORT_GENERATOR_PATH=${scriptDir}/../../

TEMPLATES_PATH=${REPORT_GENERATOR_PATH}/conf/experiments/blockchain

cp ${TEMPLATES_PATH}/report_generator_config.ini ${REPORT_GENERATOR_PATH}/conf/report_generator_config.ini
bash scripts/generate_report.sh "2023-11-05_08:59"

rm ${REPORT_GENERATOR_PATH}/conf/report_generator_config.ini

