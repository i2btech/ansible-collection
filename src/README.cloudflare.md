# Cloudflare

## Bulk Redirects

Manage and synchronize Cloudflare Bulk Redirect Lists by reading target/source pairs from a CSV file.

- Skips home URLs (root paths) automatically to prevent redirect loops.
- Handles duplicate entries and asynchronous bulk operations in Cloudflare.
- Automatically exports a backup CSV to Google Drive (uses `credential.json` by default).
- Has a 10-redirect safety limit (override with `force_bulk: true`).
- Requires an API Token with permissions to edit Bulk Redirects.