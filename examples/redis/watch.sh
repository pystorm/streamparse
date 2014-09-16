#!/bin/bash
redis-cli flushall && watch -n 0.2 python tools/redis_watch.py
