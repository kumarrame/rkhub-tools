# Third-Party Notices

RKHUB Tools vendors the following libraries **locally** (no CDN, no third-party
network request at runtime). Each file keeps its original licence header intact.

---

## pdf-lib 1.17.1

* **File:** `static/vendor/pdf-lib.min.js`
* **Project:** https://github.com/Hopding/pdf-lib
* **Upstream licence:** MIT (Copyright (c) 2017-2021 Hopping, LLC and contributors)
* **Size:** 525,099 bytes
* **SHA-384:** `weMABwrltA6jWR8DDe9Jp5blk+tZQh7ugpCsF3JwSA53WZM9/14PjS5LAJNHNjAI`

> **Note on embedded third-party code.**
> The upstream bundle embeds a compression/decompression routine carrying
> *"Copyright (c) Microsoft Corporation. All rights reserved."* licensed under
> the **Apache License, Version 2.0**. That notice is preserved verbatim inside
> the vendored file. It is not relicensed by this project.

## jsPDF 2.5.1 (UMD build)

* **File:** `static/vendor/jspdf.umd.min.js`
* **Project:** https://github.com/parallax/jsPDF
* **Upstream licence:** MIT (Copyright (c) 2010-2022 James Hall and contributors)
* **Size:** 364,463 bytes
* **SHA-384:** `JcnsjUPPylna1s1fvi1u12X5qjY5OL56iySh75FdtrwhO/SWXgMjoVqcKyIIWOLk`

jsPDF bundles further third-party components whose notices are retained in the
file, including work by yWorks GmbH, Lukas Holländer, Aras Abbasi, Aaron Spike,
Willow Systems Corporation, Pablo Hess, Florian Jenett and Warren Weckesser.

---

## Why vendored

Scripts were previously loaded from `cdnjs.cloudflare.com` at runtime. That meant:

1. Every visitor's IP address, user agent and referrer were disclosed to a third party.
2. A compromise of the CDN could execute arbitrary code on every visitor's page.
3. Three extra DNS + TLS round-trips before any tool could load.

Vendoring removes the third-party request entirely, so no visitor IP, user agent
or referrer is disclosed to anyone but the site itself, and no third-party
script can execute on a visitor's page. This is what makes the "files never
leave your device" claim on the site actually true.

> **Note on cache headers.** These files are served with
> `Cache-Control: public, max-age=600, must-revalidate` rather than a one-year
> `immutable` policy, because their URLs are *not* content-hashed
> (`pdf-lib.min.js`, not `pdf-lib.<hash>.min.js`). A long `immutable` lifetime
> on an unhashed name would leave returning visitors pinned to a stale bundle
> after an upgrade. Raise the max-age only if the filenames start carrying a
> content hash.

## Verifying integrity

```powershell
Get-FileHash static\vendor\pdf-lib.min.js  -Algorithm SHA384
Get-FileHash static\vendor\jspdf.umd.min.js -Algorithm SHA384
```

Compare the base64 suffix against the values above. To upgrade, update the file,
recompute both hashes, and re-run the tool smoke tests.
