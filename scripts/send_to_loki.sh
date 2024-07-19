#!/bin/bash

set -e

start_time=$START_TIME
address=$LOKI_ADDRESS
username=$LOKI_USERNAME
password=$LOKI_PASSWORD

current_time=$(date +%s)
duration=$(($current_time - $start_time))

nanosecond_time="${current_time}000000000"

echo "labels: $LABELS"
labels=$(echo $LABELS | jq .)

IFS="/" read -ra ADDR <<<"$REPOSITORY"
REPOSITORY_OWNER="${ADDR[0]}"
REPOSITORY_NAME="${ADDR[1]}"

log_msg="workflow=\"$WORKFLOW\" \
repository_owner=\"$REPOSITORY_OWNER\" \
repository_name=\"$REPOSITORY_NAME\" \
status=\"$STATUS\" \
run_number=$RUN_NUMBER \
actor=\"$ACTOR\" \
url=\"$URL\" \
ref=\"$REF\" \
duration=$duration"

if [ ! -z "$VALUES" ]; then
    log_msg="$log_msg $VALUES"
fi

log_entry=$(
    jq -n \
        --arg nanosecond_time "$nanosecond_time" \
        --arg message "$log_msg" \
        '{
            "streams": [
                {
                    "stream": {
                        "job": "github-actions",
                        "level": "info",
                    },
                    "values": [
                        [$nanosecond_time, $message]
                    ]
                }
            ]
        }'
)

echo "Sending log entry to Loki:"
echo $log_entry

echo $log_entry | curl -f -X POST -H "Content-Type: application/json" -d @- -u $username:$password $address/loki/api/v1/push || exit 1
