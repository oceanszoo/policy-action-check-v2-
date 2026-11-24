# Security policy

Please report security problems privately through GitHub:
**Security** tab -> **Report a vulnerability** (private security advisory). Do not open a public
issue for a vulnerability.

Scope notes:

- `scripts/pac.py` and `apps/pac-reader/pac.js` read bundle files and run no model and no network
  calls. Bundles are data; a bundle that makes either engine crash, hang or run code is a security
  bug.
- The reader runs entirely in the browser and uploads nothing.
- The plugin's hooks run inside Claude Code on your machine; report any hook behaviour that goes
  beyond what the plugin README describes.
