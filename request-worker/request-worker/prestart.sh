#!/usr/bin/env bash
echo "STARTING request worker"
echo "starting redis server on request worker"
redis-server --daemonize yes --replicaof redis_master 6379
./wait-for-it.sh ${HOST_BROKER}:5672 -t 0