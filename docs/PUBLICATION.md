# Publication safety

Public evidence is a deterministic allowlisted projection from a more detailed private receipt. Unknown
private fields fail closed; publication is not a manual redaction exercise. The envelope, the projector,
and its refusal reasons are published in [private superset and public projection](PROJECTION.md); a
producer's own receipts, storage, and CI stay in the producer's repository.

`evidence project` refuses a private record that would leak, drift, echo private material, or publish media
without a verified-clear grant. `evidence package` validates every JSON document, rejects symbolic links and
unsupported file types, scans field names and values for common secrets/private paths/endpoints, and writes
a deterministic archive.

The scan is deliberately conservative and cannot prove privacy or licensing. A first official release
still needs human review of:

- exact media and output grants;
- customer/participant de-identification;
- hidden-label and train/evaluation separation;
- model/checkpoint/API/codec rights;
- failures, exclusions, retries, and manual work; and
- claims made by the accompanying page or video.

Demonstration samples are permanently exposed and must not later become sealed-primary evidence.

## Proprietary implementation review

`evidence disclosure-review PATH` adds a separate heuristic review of Markdown, JSON, HTML,
text, YAML, and common model assets. It reports concrete model/training recipes, combined numeric
frame-sampling/JPEG settings, and private Tailscale service references. Results contain only file
locations and categories. This narrow scan misses paraphrases, code, images, other binary formats,
and other implementations; a clean result does not prove intellectual-property secrecy.

The default is `observe`: findings are reported with exit code 0. `enforce` returns exit code 1
when findings remain; invalid configuration or unreadable inputs return exit code 2. Pass a private
JSON controls file with `--controls /private/disclosure-controls.json`:

```json
{
  "enabled": true,
  "mode": "enforce",
  "recipes": true,
  "private_references": true,
  "model_assets": true,
  "reviewed_sha256": []
}
```

`enabled: false` is the master off switch; `mode: "off"` also skips the scan. Each of `recipes`,
`private_references`, and `model_assets` independently disables its category. Unknown keys and
malformed values fail even when disabled. These switches do not disable existing credential,
projection, schema, or media-rights checks. Hidden directories, generated `dist` content,
`node_modules`, and `__pycache__` are excluded; scan any intended publication directory explicitly.
Symlinks, oversized files, and undecodable text are reported as unreviewed.

Only an owner-reviewed exact file SHA256 digest should enter `reviewed_sha256`. An edit invalidates
that approval. Previous public availability is not implicit approval, and the tooling never adds
approvals automatically. Forgejo currently reports findings in observe mode while the owner decides
which existing disclosures to retain or redact. The scan does not remove public documents, rewrite
Git history, or retract copies already distributed. Review the intended publication and its history
before enabling a blocking policy.
