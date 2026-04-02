# Security Policy

## Reporting a Vulnerability

If you discover a security vulnerability in MAESTRO AI, please **do not** open a public GitHub issue.

Instead, report it privately:

- Email: security@lrrecords.com.au (preferred)
- Or: email brett@lrrecords.com.au if the security address isn’t available

Please include:
- A clear description of the issue and potential impact
- Steps to reproduce (proof-of-concept if possible)
- Any relevant logs, screenshots, or code pointers

## Scope / Notes

MAESTRO AI is a self-hosted app intended to run locally or in your own infrastructure.

**Never commit secrets** (API keys, tokens, passwords) to this repository.
Use `.env` (see `.env.example`) and keep your `.env` out of git.