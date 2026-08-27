# Evidence site source

The site has two kinds of content and treats them differently.

**Prose is authored.** The doctrine, the boundary statement, and what evidence must show are written by
hand and reviewed like any other copy.

**The release index is generated.** Everything between the generated markers in `site/index.html` is a
deterministic allowlisted projection of `registry/official.json` and `registry/community.json`:

```bash
python tools/render_site.py
```

`tests/test_site.py` fails if the checked-in page differs from that projection, so the page cannot claim
a release the registries do not carry — nor keep claiming there are none once they do.

That distinction is the point. Before this, the page asserted "there are no official KhelSutra quality
releases yet" as hand-typed prose sitting next to the data. The first registry entry would have made the
sentence false, and nothing would have noticed. It is now rendered *from* the registry, so an empty
registry is why the page says the registry is empty.

## What the renderer refuses

| Refused | Why |
|---|---|
| a release reference carrying a field outside the allowlist | a field nobody allowlisted is a field nobody reviewed |
| a `digest` object carrying anything but `algorithm` and `value` | the same rule, one level down |
| any projected value that fails the public-safety scan | the site is a publication surface like any other |
| a registry that fails `EvidenceRegistryV1` or declares the wrong `registry` | official and community separation is structural, not filename-deep |

Registry values are HTML-escaped, so a release id or media type containing markup renders as text rather
than becoming part of the page.

## The release data digest

The generated block ends with the SHA-256 of the canonical projection it rendered — sorted keys, no
insignificant whitespace. A reader can recompute it from the registries and confirm the page shows
exactly that data and nothing else. It moves when the registry data moves, and only then.

It is a digest of the *release data*, not of the repository. Binding the page to a source revision as
well belongs with a deployment that has a revision to bind, which does not exist yet.

## What is not done here

No site is deployed, and no domain is claimed. Publication needs explicit infrastructure authority and a
source-driven deployment path — external gate 6 in [the tracker](PROJECT.md). This row delivers the
source and its guarantees; it does not put anything on the internet.
