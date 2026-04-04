---
name: "@tank/kubectl-cheatsheet"
description: |
  Fast kubectl command reference for day-to-day Kubernetes operations. Covers
  core kubectl verbs (`get`, `describe`, `logs`, `exec`, `apply`, `delete`,
  `scale`, `rollout`, `top`, `port-forward`), resource-focused usage (pods,
  deployments, services, nodes, namespaces, configmaps, secrets), output
  formatting, selectors, debugging, and high-frequency operational commands.

  Synthesizes Kubernetes official kubectl documentation, kubectl reference,
  common operator workflows, and production command patterns.

  Trigger phrases: "kubectl", "kubectl cheat sheet", "kubectl commands",
  "kubectl get pods", "kubectl logs", "kubectl exec", "kubectl apply",
  "kubectl port-forward", "kubectl rollout", "kubectl scale", "kubectl top"
---

# Kubectl Cheat Sheet

## Core Philosophy

1. **Optimize for the command you need right now** — Cheat sheets should get you to the right command quickly, not explain Kubernetes from first principles.
2. **Group by operational task, not alphabetically** — Operators think in “inspect pods” and “roll out a deployment,” not in raw verb order.
3. **Prefer safe read commands first** — `get`, `describe`, `logs`, and `diff` should come before write actions when debugging.
4. **Make selectors and namespaces explicit** — Most kubectl mistakes come from targeting the wrong objects or cluster scope.
5. **Include output shaping** — `-o wide`, `-o yaml`, `jsonpath`, and label selectors often matter as much as the base command.

## Quick-Start: Common Problems

### "What pods are broken right now?"

1. `kubectl get pods -A`
2. `kubectl describe pod <pod> -n <ns>`
3. `kubectl logs <pod> -n <ns> --previous`
-> See `references/commands.md`

### "How do I restart or roll out a deployment?"

| Need | Command |
|------|---------|
| restart deployment | `kubectl rollout restart deploy/<name> -n <ns>` |
| watch rollout status | `kubectl rollout status deploy/<name> -n <ns>` |
| scale replicas | `kubectl scale deploy/<name> --replicas=3 -n <ns>` |
-> See `references/commands.md`

## Decision Trees

| Signal | Command family |
|--------|----------------|
| need to inspect objects | `get`, `describe`, `logs`, `top` |
| need to enter or reach workload | `exec`, `port-forward` |
| need to change desired state | `apply`, `delete`, `scale`, `rollout` |
| need filtered output | selectors, `-o`, `jsonpath` |

## Reference Index

| File | Contents |
|------|----------|
| `references/commands.md` | kubectl commands grouped by inspect, debug, mutate, rollout, output shaping, namespaces, resources, and common operator tasks |
