#!/usr/bin/env bash
source /home/jonatan/development/BDWatchdog/set_pythonpath.sh
pdoc3 --html --template-dir templates/ --force ../src -o code

#pdoc3 --html --template-dir templates/ --force ../src/Guardian ../src/Rescaler -o code/
#cp templates/index.html code/index.html