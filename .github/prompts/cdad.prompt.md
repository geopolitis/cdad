# CDAD Agent Command

Use CDAD artifacts as the operating boundary for this task.

1. Read `agent/memory/project.md`.
2. Read the selected packet under `agent/packets/`.
3. Run `cdad validate --strict-paths` before implementation.
4. Build a compact context bundle with `cdad context <TASK_ID>`.
5. Implement only the packet objective.
6. Run `cdad verify <TASK_ID>`.
7. Append progress with `cdad progress add <TASK_ID> ...`.
8. Escalate dependency, schema, contract, security, destructive, or scope-widening changes.

Do not treat this command as a giant prompt. The packet is the runtime source.
