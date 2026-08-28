# Private contract examples

`MediaGrantV1` and `PrivateEvidenceRecordV1` are contracts a producer holds; they are never published.
They live here rather than in `examples/` for one concrete reason: `evidence package` refuses a private
schema, so an `examples/` directory containing one is an example set the framework cannot package.

`evidence verify` still validates everything here — being unpublishable is not the same as being
unchecked. The split is about what may leave the machine, not about what must be correct.
