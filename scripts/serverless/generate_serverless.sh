#!/usr/bin/env bash
scriptDir=$(dirname -- "$(readlink -f -- "$BASH_SOURCE")")

export REPORT_GENERATOR_PATH=${scriptDir}/../../


TEMPLATES_PATH=${REPORT_GENERATOR_PATH}/conf/experiments/templates/serverless

cp ${TEMPLATES_PATH}/microbenchmarks/report_generator_config.ini ${REPORT_GENERATOR_PATH}/conf/report_generator_config.ini
#bash scripts/generate_report.sh 00:00_PR
#bash scripts/generate_report.sh 01:00_PR
#bash scripts/generate_report.sh 03:00_PR
bash scripts/generate_report.sh 02:00_PR #CHOSEN

cp ${TEMPLATES_PATH}/streaming/report_generator_config.ini ${REPORT_GENERATOR_PATH}/conf/report_generator_config.ini
#bash scripts/generate_report.sh 00:00_FW
#bash scripts/generate_report.sh 01:00_FW
bash scripts/generate_report.sh 02:00_FW #CHOSEN

cp ${TEMPLATES_PATH}/hybrid/report_generator_config.ini ${REPORT_GENERATOR_PATH}/conf/report_generator_config.ini
#bash scripts/generate_report.sh 00:00_HYBRID
#bash scripts/generate_report.sh 01:00_HYBRID
#bash scripts/generate_report.sh 02:00_HYBRID
bash scripts/generate_report.sh 03:00_HYBRID #CHOSEN

cp ${TEMPLATES_PATH}/concurrent/report_generator_config.ini ${REPORT_GENERATOR_PATH}/conf/report_generator_config.ini
#bash scripts/generate_report.sh 00:00_CONCURRENT
bash scripts/generate_report.sh 01:00_CONCURRENT #CHOSEN
