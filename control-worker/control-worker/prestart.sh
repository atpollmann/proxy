#!/usr/bin/env bash
echo "STARTING CONTROL WORKER"
./wait-for-it.sh ${HOST_BROKER}:5672 -t 0 -- python main.py