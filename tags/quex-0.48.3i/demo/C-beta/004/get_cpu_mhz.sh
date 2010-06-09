# Gets the CPU frequency from the /proc/ directory
# (currently only for linux)
cat /proc/cpuinfo  | awk '/cpu MHz/ { print $4; exit; }'
