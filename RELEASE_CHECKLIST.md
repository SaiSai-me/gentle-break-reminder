# Release Checklist

## Local release

- [ ] Manifest uses a clean semantic version with no local cache-buster.
- [ ] Manifest, skill, paths, and assets pass plugin validation.
- [ ] Unit tests and Python compilation pass.
- [ ] Privacy claims match the implementation and tests.
- [ ] Repository contains no secrets, local state, transcripts, or generated caches.
- [ ] README, changelog, privacy policy, terms, and submission materials match the release.

## GitHub release

- [ ] Public repository created under the intended GitHub account.
- [ ] Default branch is `main` and branch protection/settings are reviewed.
- [ ] Private vulnerability reporting is enabled when available.
- [ ] Tag and GitHub Release use `v0.1.2`.
- [ ] Release archive contains the same file tree that passed local testing.
- [ ] Public repository, policy, support, and release URLs resolve without authentication.

## OpenAI submission

- [ ] Submitter has Apps Management: Write in the selected OpenAI organization.
- [ ] Developer or business identity is verified in the same organization.
- [ ] Submission type is Skills only.
- [ ] Final skill bundle from the tagged release is uploaded.
- [ ] Three starter prompts are entered.
- [ ] Five positive and three negative tests are entered with expected behavior.
- [ ] Country and region availability is intentionally selected.
- [ ] Release notes and policy attestations are reviewed before submission.
