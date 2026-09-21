# Locally bundled import parsers

- SheetJS Community Edition 0.20.3: https://cdn.sheetjs.com/xlsx-0.20.3/package/dist/xlsx.full.min.js (Apache-2.0; xlsx-LICENSE.txt).
- Papa Parse 5.5.3: https://cdn.jsdelivr.net/npm/papaparse@5.5.3/papaparse.min.js (MIT; papaparse-LICENSE.txt).

These pinned files are served locally. There are no runtime CDN requests, keys, or inference services. XLSX archive expansion is bounded before the workbook parser runs. Financial values remain text until explicit Decimal normalization. Neither library owns financial calculations.

- `xlsx.full.min.js` SHA-256: `cc015130aa8521e7f088f88898eba949ccdcbfb38df0bd129b44b7273c3a6f41`
- `papaparse.min.js` SHA-256: `3553fb8bdf5b8004ce5531e6827e81c8b34e7b3992677967754544064e97b016`
