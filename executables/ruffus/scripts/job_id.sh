#!/bin/bash
set -e
set -x
JOBID=$(date +%y%m%d%H%M%S)

# plain xargs trims spaces:
BASEDIR=$(grep BASEDIR input.ini | cut -d"=" -f 2 | xargs)
FOLDER=$BASEDIR/$JOBID


cp input.ini output.ini

# if the last line in output.ini is not completed with \n the JOB_ID
# entry below would not write to a new line, so we enforce the \n:
echo >> output.ini
echo "JOB_ID = $JOBID" >> output.ini

echo
echo output.ini:
cat output.ini
