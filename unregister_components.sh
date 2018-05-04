#!/bin/bash

ps -ef | grep "python -m" | while read pps; do
    pid=$( echo $pps | awk '{printf $2}' )
    kill $pid
done