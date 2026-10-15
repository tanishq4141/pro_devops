#!/usr/bin/env bash
# Generate CPU load on the backend so the HPA scales out.
#   ./scripts/load-test.sh                     # in-cluster, 6 workers for 180s
#   WORKERS=10 DURATION=300 ./scripts/load-test.sh
set -euo pipefail
NS="${NS:-stockpilot}"
TARGET="${TARGET:-http://stockpilot-backend.${NS}.svc.cluster.local:8000/api/products/stats}"
WORKERS="${WORKERS:-6}"
DURATION="${DURATION:-180}"

echo "Hitting ${TARGET} with ${WORKERS} workers for ${DURATION}s"
for i in $(seq 1 "$WORKERS"); do
  kubectl run "load-${i}" -n "$NS" --rm -i --restart=Never --image=busybox:1.36 --quiet -- \
    sh -c "end=\$((\$(date +%s)+${DURATION})); while [ \$(date +%s) -lt \$end ]; do wget -q -O- ${TARGET} >/dev/null; done" &
done
echo "Watch it scale:  kubectl get hpa -n ${NS} -w"
wait
echo "Load test completed"
