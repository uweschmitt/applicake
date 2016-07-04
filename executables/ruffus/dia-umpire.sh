#!/bin/bash

# to call this script provide path to mzXML file as first argument you can
# provide an optional paramfile as second argument if you have special
# requirements.

set -x

# next line is from:
# http://stackoverflow.com/questions/4774054/reliable-way-for-a-bash-script-to-get-the-full-path-to-itself

ABSOLUTE_PATH="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/$(basename "${BASH_SOURCE[0]}")"

HERE=$(dirname $ABSOLUTE_PATH)

# we know where we installed dia umpire relative to this script:
DIA_UMPIRE_PATH=$HERE/../dia-umpire
DIA_JAR=$DIA_UMPIRE_PATH/DIA_Umpire_SE.jar

# either the user specifies a path to a parameter file for dia umpire or we use
# a standard file:

STD_PARAMETER_FILE=$DIA_UMPIRE_PATH/diaumpire_se.params
PARAMETER_FILE=${2:-$STD_PARAMETER_FILE}
echo "USE PARAMETER FILE $PARAMETER_FILE"

# we cd to the folder with the incoming data file, so all results will be
# written next to this file:

DATAFOLDER=$(dirname $1)
pushd $DATAFOLDER

# run dia umpire
INPUTFILE=$(basename $1)


if [ ${INPUTFILE: -9} != ".mzXML.gz" ]; then
    if [ ${INPUTFILE: -6} != ".mzXML" ]; then
        echo "need .mzXML or .mzXML.gz file as input"
        exit 1
    fi
fi

# unzip gzipped file
if [ ${INPUTFILE: -3} == ".gz" ];
then
    gunzip $INPUTFILE
    INPUTFILE=${INPUTFILE%.gz}
fi


java -Xmx24G -jar $DIA_JAR $INPUTFILE $PARAMETER_FILE

# convert mgf to mzXML files
for MGF in *.mgf; do
    msconvert --mzXML $MGF
done;

STEM=${INPUTFILE%.mzXML}

# we copy the used parameter file next to the result:
cp $PARAMETER_FILE .

# we gzip the mzXML fieles and compute the md5 checksums. when gzipping we use
# -n to avoid storing time stamp data to the compressed files, else the md5
# checksum for same data files will differ.

for U in ${STEM}_Q?.mzXML; do
    gzip -n -f $U
    md5sum $U.gz > $U.gz.md5
done

# undo cd to folder with data files
popd
