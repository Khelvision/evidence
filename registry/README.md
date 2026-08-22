# Release registries

- `official.json` contains releases published and signed off through the KhelSutra evidence programme.
- `community.json` contains self-run evidence that passed contract and safety review.

Both files implement `EvidenceRegistryV1`, use the same `releases` collection of content-addressed
release references, and carry an explicit `official` or `community` discriminator. `evidence verify
registry` validates the separation rather than relying on filenames or prose.

Community registration is not official verification, endorsement, licence clearance, or a quality award.
The framework preview starts with both registries empty.
