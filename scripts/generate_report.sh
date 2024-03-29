#!/usr/bin/env bash

if [[ -z ${2} ]];
then
	echo "2 arguments are needed"
	echo " + The name of the experiment to generate is needed"
	echo " + The path to the configuration file to use"
	exit 1
fi


scriptDir=$(dirname -- "$(readlink -f -- "$BASH_SOURCE")")
source ${scriptDir}/../set_pythonpath.sh

export REPORT_GENERATOR_PATH=${scriptDir}/../

LATEX_TEMPLATE=${REPORT_GENERATOR_PATH}/latex/simple_report.template
OUTPUT_REPORTS_FOLDER=$REPORT_GENERATOR_PATH/REPORTS

mkdir -p ${OUTPUT_REPORTS_FOLDER}/$1
cp $2 ${OUTPUT_REPORTS_FOLDER}/$1/report_generator_config.ini
cd ${OUTPUT_REPORTS_FOLDER}/$1

echo "Generating report for experiment $1"
python3 ${REPORT_GENERATOR_PATH}/src/main.py $1 > $1.txt
if [[ $? -eq 0 ]]
then
    pandoc $1.txt --pdf-engine=xelatex --variable=fontsize:8pt --number-sections --toc --template ${LATEX_TEMPLATE} -o $1.pdf
    if [[ $? -eq 0 ]]
    then
        echo "Successfully generated report"
    fi
    rm -f *.eps
fi

cd $REPORT_GENERATOR_PATH