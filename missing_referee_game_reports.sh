#!/bin/bash

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
cd $SCRIPT_DIR
source $SCRIPT_DIR/venv/bin/activate
python $SCRIPT_DIR/src/missing_game_reports.py -r 2>&1 | tee -a /var/log/cysl/missing_game_report.log
