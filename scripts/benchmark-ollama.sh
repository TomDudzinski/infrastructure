#!/usr/bin/env bash

set -euo pipefail

MODEL="${1:-llama3.2:1b}"
PROMPT="${2:-Napisz krótki opis Polski w pięciu zdaniach.}"

response="$(
  curl --silent --fail http://127.0.0.1:11434/api/generate \
    --header "Content-Type: application/json" \
    --data "$(jq -n \
      --arg model "$MODEL" \
      --arg prompt "$PROMPT" \
      '{
        model: $model,
        prompt: $prompt,
        stream: false
      }')"
)"

eval_count="$(jq -r '.eval_count // 0' <<< "$response")"
eval_duration="$(jq -r '.eval_duration // 0' <<< "$response")"
load_duration="$(jq -r '.load_duration // 0' <<< "$response")"
total_duration="$(jq -r '.total_duration // 0' <<< "$response")"

if (( eval_duration > 0 )); then
  tokens_per_second="$(
    awk -v count="$eval_count" -v duration="$eval_duration" \
      'BEGIN { printf "%.2f", count / (duration / 1000000000) }'
  )"
else
  tokens_per_second="0"
fi

echo "Model:              $MODEL"
echo "Generated tokens:   $eval_count"
echo "Tokens per second:  $tokens_per_second"
echo "Load time:          $(awk -v n="$load_duration" 'BEGIN {printf "%.2f s", n/1000000000}')"
echo "Total time:         $(awk -v n="$total_duration" 'BEGIN {printf "%.2f s", n/1000000000}')"
echo
echo "Response:"
jq -r '.response' <<< "$response"x
