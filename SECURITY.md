# Security

This project processes medical and medication-related information. Treat uploaded documents, prescriptions, API keys, OAuth credentials, Neo4j credentials, and generated reports as sensitive.

## Do not commit

- `.env` files or copied secrets;
- Google OAuth client secrets or token files;
- Neo4j passwords and connection strings containing credentials;
- real patient prescriptions or personally identifiable information;
- private raw datasets and generated exports unless explicitly approved.

Use the supplied `.env.example` files as templates. The root `.gitignore` is intentionally strict, but check `git status` before every commit.

## If a secret was committed

1. Revoke or rotate it immediately in the provider that issued it.
2. Remove it from the working tree and Git history using an approved history-rewrite process.
3. Notify the repository owners and document the remediation.

Removing a file in a new commit does not remove a secret from old Git history.

## Reporting a vulnerability

Do not open a public issue with credentials, patient data, or exploit details. Contact the repository owner privately with the affected component, impact, reproduction steps, and any safe redaction needed.