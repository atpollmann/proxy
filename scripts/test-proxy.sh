#!/usr/bin/env bash

ITERATIONS=10
BASE_URL="http://localhost:8000/"
REQUEST_PATH="categories/MLC1652"
OPTIND=1 # Reset in case getopts has been used previously in the shell.

info () {
	echo -e "\033[0;33m$1\033[0m"
} && export -f info

error () {
	echo -e "\033[0;31m$1\033[0m"
} && export -f error

success () {
	echo -e "\033[0;32m$1\033[0m"
} && export -f success

show_help () {
cat <<EOF

Proxy tester
-----------------------

Test the meli proxy. It delivers only the status of the requests.

Usage: test-proxy.sh [-p][-c]

    -p : Path to test. No leading slash. Defaults to categories/MLC1652
    -c : How many requests to make. Defaults to 10

EOF
}

while getopts "h?:p:c:" opt; do
    case "$opt" in
		h|\?)
        show_help
        exit 0
        ;;
    p)
        REQUEST_PATH=$OPTARG
        ;;
    c)
        ITERATIONS=$OPTARG
        ;;
    esac
done

shift $((OPTIND-1))

[ "${1:-}" = "--" ] && shift

for ((i = 0 ; i <= ${ITERATIONS} ; i++)); do
  info "GET ${BASE_URL}${REQUEST_PATH}"
  curl -I ${BASE_URL}${REQUEST_PATH}
done