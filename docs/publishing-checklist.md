# Publishing checklist

Before making the repository public:

- [ ] Run `git status --short` and inspect every staged file.
- [ ] Confirm no `.env`, OAuth client secret, token, password, or private key is tracked.
- [ ] Confirm no patient prescription or personally identifiable information is included.
- [ ] Confirm full DrugBank XML and other licensed/private datasets are excluded.
- [ ] Run the relevant Python syntax and import checks for each application.
- [ ] Review third-party licenses and data-use terms.
- [ ] Replace placeholder names, URLs, and credentials in public documentation.
- [ ] Add a license once the project owners choose one.
- [ ] Configure CI for the checks that are expected to remain green.
- [ ] Confirm whether the final UI repository may be linked or whether screenshots are sufficient.
- [ ] Review all UI screenshots for real patient data, internal URLs, browser state, and private identifiers.
- [ ] Obtain coworker approval before linking or publishing UI assets.
- [ ] Confirm RAGFlow prompts, datasets, embeddings, and VM setup are described without exposing private configuration.
- [ ] Remove RAGFlow API keys, VM addresses, model credentials, and internal endpoints from documentation.
- [ ] Confirm any external UI or RAG repository is licensed and owned by an authorized contributor.

If a secret has ever been committed, rotate it and clean Git history before publishing. A new ignore rule does not remove an old secret from history.
