# Publication safety

Public evidence is designed to be a deterministic allowlisted projection from a more detailed private
receipt. Unknown private fields fail closed; publication is not a manual redaction exercise. The private
projector is a separate gated integration: this framework preview validates only already-projected public
documents and must not be pointed at an arbitrary private receipt.

`evidence package` validates every JSON document, rejects symbolic links and unsupported file types, scans
field names and values for common secrets/private paths/endpoints, and writes a deterministic archive.

The scan is deliberately conservative and cannot prove privacy or licensing. A first official release
still needs human review of:

- exact media and output grants;
- customer/participant de-identification;
- hidden-label and train/evaluation separation;
- model/checkpoint/API/codec rights;
- failures, exclusions, retries, and manual work; and
- claims made by the accompanying page or video.

Demonstration samples are permanently exposed and must not later become sealed-primary evidence.
