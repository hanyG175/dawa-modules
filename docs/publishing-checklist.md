# Publishing checklist

Before making the repository public:

- [ ] Run `git status --short` and inspect every staged file.
- [ ] Confirm no `.env`, OAuth client secret, token, password, or private key is tracked.
- [ ] Confirm no patient prescription or personally identifiable information is included.
- [ ] Confirm full DrugBank XML and other licensed/private datasets are excluded.
- [ ] Run the relevant Python syntax/import checks.
- [ ] Run the relevant Python syntax and import checks for each application.
- [ ] Review third-party licenses and data-use terms.
- [ ] Replace placeholder names, URLs, and credentials in public documentation.
- [ ] Add a license once the project owners choose one.
- [ ] Configure CI for the checks that are expected to remain green.

If a secret has ever been committed, rotate it and clean Git history before publishing. A new ignore rule does not remove an old secret from history.
