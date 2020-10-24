#!/bin/bash


# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
PLAIN='\033[0m'
BOLD=$(tput bold)
TAG="${BOLD}[ TEST ]${PLAIN}"

for dir in $(ls data/); do
    for file in $(ls data/$dir | grep -Eo "(merged_[0-9].*)" | sort -u); do
        err=$(cat data/$dir/$file | tail -f -n 1 | grep -Eo "(\,{2,6})")
        echo -e "$TAG Testing file $file from data/$dir"
        if [[ ! $err ]]; then
            echo -e "$TAG $GREEN PASSED! $PLAIN"
        else
            echo -e "$TAG $RED FAILED $PLAIN"
            echo $(cat data/$dir/$file | grep -Eo ".*(\,{2,6})")
        fi
    done
done
