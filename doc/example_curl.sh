#!/bin/bash

# init conversation, obtain vqd
#
# note: --head means "fetch headers only"
#
vqd="$(curl \
  --header 'Accept-Encoding: gzip, deflate' \
  --header 'Accept: */*' \
  --header 'Connection: keep-alive' \
  --header 'x-vqd-accept: 1' \
  --head \
  --http1.1 \
  --verbose \
  --output /dev/null \
  --write-out '%header{x-vqd-4}' \
  \
  https://duckduckgo.com/duckchat/v1/status
)"

printf "vqd: %s\n" "${vqd}"

# Send prompt
curl -X POST \
  --header 'Accept-Encoding: gzip, deflate' \
  --header 'Accept: text/plain' \
  --header 'Connection: keep-alive' \
  --header "x-vqd-4: ${vqd}" \
  --header 'Content-Type: application/json' \
  --http1.1 \
  -d '{"model":"gpt-4o-mini","messages":[{"content":"test","role":"user"}]}' \
  --verbose \
  \
  https://duckduckgo.com/duckchat/v1/chat
