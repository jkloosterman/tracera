#!/bin/bash -xe
#
# Run the trace generation Pintool.

SQLITE3=sqlite3
PIN=~/pin/pin
PINTOOL=~/tracera/trace_generator/obj-intel64/trace_generator.so
CREATE_INDICES=~/tracera/scripts/create_indices.sql

if [ -z "$1" ];
then
    echo "trace.sh <annotated executable> <arguments for executable>"
    exit 1
fi
shift

echo "Tracing $1..."
echo "Generating trace..."
time $PIN -injection child -t $PINTOOL -df /tmp/$$.sqlite -- $@
echo "Creating indices..."
time sqlite3 /tmp/$$.sqlite < $CREATE_INDICES

mv /tmp/$$.sqlite trace.sqlite

echo "Done."
