#!/usr/bin/env bash
echo "starting redis server"
redis-server --daemonize yes --replicaof redis_master 6379