#!/usr/bin/sh
# Set LOG_LEVEL
export LOG_LEVEL=error
echo "hi"
# Start service
exec "$@"