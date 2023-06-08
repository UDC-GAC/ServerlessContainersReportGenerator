#!/usr/bin/env bash
scriptDir=$(dirname -- "$(readlink -f -- "$BASH_SOURCE")")

export REPORT_GENERATOR_PATH=${scriptDir}/../
source $REPORT_GENERATOR_PATH/set_pythonpath.sh

LATEX_TEMPLATE=${REPORT_GENERATOR_PATH}/latex/templates/simple_report.template
OUTPUT_REPORTS_FOLDER=$REPORT_GENERATOR_PATH/REPORTS

if [[ -z ${1} ]];
then
	echo "The name of the experiment to generate is needed"
	exit 1
fi


echo "Generating report for experiment $1"
mkdir -p ${OUTPUT_REPORTS_FOLDER}/$1
cd ${OUTPUT_REPORTS_FOLDER}/$1
python3 ${REPORT_GENERATOR_PATH}/src/report_generator.py $1 > $1.txt
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