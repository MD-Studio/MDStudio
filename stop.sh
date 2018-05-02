#!/usr/bin/env bash

# temporal ugly hack to kill all register lie microservices
ps axf | grep python | grep lie | awk '{print "kill -9 " $1}' | sh

# stop docker components
docker-compose down

