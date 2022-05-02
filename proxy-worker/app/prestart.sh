#!/usr/bin/env bash
echo "RUNNING redis-server"
redis-server --daemonize yes --replicaof redis_master 6379