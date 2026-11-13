/**
 * site.js — what the pages (viewer, gallery, lecture) and the widget's Link
 * dialog have in common: where the snippets are, and which snippet an
 * address in a link leads to.
 *
 * An address is what stands after "viewer.html?", for example
 * prgh-lectures/frl07/sortering. snippets/addresses.json lists every address
 * each snippet has ever had (create_index.py and snippet_addresses.py write
 * it; see "Addresses" in README.md). All of these lead to the same snippet:
 *
 *   viewer.html?prgh-lectures/frl07/sortering              its name
 *   viewer.html?prgh-lectures/frl07/03-example             a name it had before
 *   viewer.html?src=prgh-lectures/frl07/03-example.json    links from before names
 *   viewer.html?src=prgh-lectures%2Ffrl07%2F03-example.json
 *
 * Nothing in this file knows about particular courses or snippets, and no
 * other file says where the snippets are: SNIPPETS_DIR below is the one
 * place to change if the content moves.
 */
(function () {
  'use strict';

  // document.currentScript is only available while the script first runs
  const scriptSrc    = document.currentScript?.src || location.href;
  const SITE_URL     = new URL('.', scriptSrc).href;
  const SNIPPETS_DIR = 'snippets/';
  const SNIPPETS_URL = new URL(SNIPPETS_DIR, SITE_URL).href;

  let _bookPromise  = null;
  let _indexPromise = null;

  // ── The address list (loaded once) ─────────────────────────────────────────
  // Without the list (a copy of the site that has none, or a failed request)
  // every address is taken to be a file path, as it was before names.
  function loadBook() {
    if (_bookPromise) return _bookPromise;
    _bookPromise = fetch(SNIPPETS_URL + 'addresses.json')
      .then(r => (r.ok ? r.json() : {}))
      .catch(() => ({}))
      .then(data => {
        const book = { files: new Map(), lower: new Map(), handedOut: new Map(),
                       retired: new Set(data.retired || []) };
        for (const [file, entry] of Object.entries(data.snippets || {})) {
          const addresses = entry.addresses || [];
          if (addresses.length) book.handedOut.set(file, addresses[0]);
          for (const address of addresses) {
            book.files.set(address, file);
            if (!book.lower.has(address.toLowerCase())) book.lower.set(address.toLowerCase(), file);
          }
        }
        return book;
      });
    return _bookPromise;
  }

  function loadIndex() {
    if (!_indexPromise) {
      _indexPromise = fetch(SNIPPETS_URL + 'index.json').then(r => {
        if (!r.ok) throw new Error(`HTTP ${r.status}`);
        return r.json();
      });
      _indexPromise.catch(() => { _indexPromise = null; });
    }
    return _indexPromise;
  }

  // ── From a file in the snippets folder to something fetch() can load ───────
  // Relative on the site's own pages (as before), absolute elsewhere.
  function srcFor(file) {
    const here = new URL('.', location.href).href;
    return (here === SITE_URL ? SNIPPETS_DIR : SNIPPETS_URL) + file;
  }

  // ... and back: the file a widget's data-src points at, or null if it is
  // not in the snippets folder (a test fixture, a file on another site).
  function fileOf(src) {
    let url;
    try { url = new URL(src, location.href).href; } catch (_) { return null; }
    if (!url.startsWith(SNIPPETS_URL)) return null;
    try { return decodeURI(url.slice(SNIPPETS_URL.length)); } catch (_) { return null; }
  }

  // ── What a link says ───────────────────────────────────────────────────────
  // "?src=folder%2F03.json" (links from before names) or "?folder/name". Other
  // things that services add to links ("&fbclid=...") are ignored.
  function addressFromQuery(search) {
    const src = new URLSearchParams(search).get('src');
    if (src) return src;
    for (const part of search.replace(/^\?/, '').split('&')) {
      if (!part || part.includes('=')) continue;
      try { return decodeURIComponent(part); } catch (_) { return part; }
    }
    return null;
  }

  // The same form as in addresses.json: no ".json", no "/" at the ends.
  function normalize(address) {
    return address.trim().replace(/^\/+|\/+$/g, '').replace(/\.json$/, '');
  }

  /**
   * Finds the snippet an address leads to. Resolves to an object with
   *   src      what to give the widget as data-src
   *   file     the file in the snippets folder (if it is one)
   *   address  the address now handed out for the snippet (if it has one)
   *   retired  true if the example was removed on purpose (no src then)
   */
  async function resolve(raw) {
    // A complete URL is used as it is, unless it points into the snippets
    // folder: then it is an address like any other.
    if (/^https?:\/\//.test(raw)) {
      const inFolder = fileOf(raw);
      if (!inFolder) return { src: raw };
      raw = inFolder;
    }
    const book = await loadBook();
    const address = normalize(raw);
    const file = book.files.get(address) ?? book.lower.get(address.toLowerCase());
    if (file) return { src: srcFor(file), file, address: book.handedOut.get(file) };
    if (book.retired.has(address)) return { retired: true };
    // Not in the list: a file path, as before
    return { src: srcFor(/\.json$/.test(raw) ? raw : raw + '.json') };
  }

  async function addressOf(file) {
    return (await loadBook()).handedOut.get(file) || null;
  }

  // ── Links to a snippet on a page of its own ────────────────────────────────
  function viewerUrl(address, base) {
    const path = address.split('/').map(encodeURIComponent).join('/');
    return (base ? base.replace(/\/$/, '') + '/' : '') + 'viewer.html?' + path;
  }

  // For the pages: href to the viewer for a file from index.json
  async function linkTo(file) {
    const address = await addressOf(file);
    return address ? viewerUrl(address) : 'viewer.html?src=' + encodeURIComponent(file);
  }

  // For the widget's Link dialog: the full address to hand out for the
  // snippet behind a data-src, or null if it has none (the dialog then
  // makes a link with ?src= as before).
  async function shareUrl(src, base) {
    const file = fileOf(src);
    const address = file && await addressOf(file);
    return address ? viewerUrl(address, base || SITE_URL) : null;
  }

  // ── Download snippets as a zip file ────────────────────────────────────────
  // The zip is made here in the browser (the site has no server). The files
  // are stored uncompressed, which keeps this to a checksum and three kinds
  // of record: see "ZIP (file format)" on Wikipedia. Every program that
  // opens zip files reads such a file.
  const CRC_TABLE = Array.from({ length: 256 }, (_, n) => {
    for (let k = 0; k < 8; k++) n = n & 1 ? 0xEDB88320 ^ (n >>> 1) : n >>> 1;
    return n >>> 0;
  });
  function crc32(bytes) {
    let crc = 0xFFFFFFFF;
    for (const b of bytes) crc = CRC_TABLE[(crc ^ b) & 0xFF] ^ (crc >>> 8);
    return (crc ^ 0xFFFFFFFF) >>> 0;
  }

  // entries: [{ path: 'folder/name/main.py', text: '...' }] → Blob
  function makeZip(entries) {
    const encoder = new TextEncoder();
    const now  = new Date();
    const time = (now.getHours() << 11) | (now.getMinutes() << 5) | (now.getSeconds() >> 1);
    const date = ((now.getFullYear() - 1980) << 9) | ((now.getMonth() + 1) << 5) | now.getDate();
    // A record: 16- and 32-bit numbers, least significant byte first
    const record = (...fields) => {
      const size = fields.reduce((sum, [bits]) => sum + bits / 8, 0);
      const view = new DataView(new ArrayBuffer(size));
      let at = 0;
      for (const [bits, value] of fields) {
        if (bits === 16) view.setUint16(at, value, true); else view.setUint32(at, value, true);
        at += bits / 8;
      }
      return new Uint8Array(view.buffer);
    };
    const parts = [], directory = [];
    let offset = 0;
    for (const entry of entries) {
      const name = encoder.encode(entry.path);
      const data = encoder.encode(entry.text);
      // Shared by the record in front of each file and the one in the
      // directory at the end: version 2.0, names in UTF-8 (flag 0x0800, for
      // å/ä/ö in file names), stored (method 0), time, checksum, sizes.
      const common = [[16, 20], [16, 0x0800], [16, 0], [16, time], [16, date],
                      [32, crc32(data)], [32, data.length], [32, data.length],
                      [16, name.length], [16, 0]];
      const header = record([32, 0x04034B50], ...common);
      parts.push(header, name, data);
      directory.push(record([32, 0x02014B50], [16, 20], ...common,
                            [16, 0], [16, 0], [16, 0], [32, 0], [32, offset]), name);
      offset += header.length + name.length + data.length;
    }
    const directorySize = directory.reduce((sum, part) => sum + part.length, 0);
    const end = record([32, 0x06054B50], [16, 0], [16, 0], [16, entries.length], [16, entries.length],
                       [32, directorySize], [32, offset], [16, 0]);
    return new Blob([...parts, ...directory, end], { type: 'application/zip' });
  }

  /**
   * Downloads the files of one or more snippets (files from index.json) as
   * zipName. Inside the zip each snippet is a directory named after its
   * address, so that it unpacks the way the examples are organised:
   *   prgh-lectures/frl07/sortering/main.py
   */
  async function downloadSnippets(files, zipName) {
    const entries = [];
    for (const file of files) {
      const response = await fetch(srcFor(file));
      if (!response.ok) throw new Error(`HTTP ${response.status} for ${file}`);
      const snippet = await response.json();
      const folder  = (await addressOf(file)) || file.replace(/\.json$/, '');
      const parts   = Array.isArray(snippet.files) && snippet.files.length
        ? snippet.files : [{ name: 'main.py', content: snippet.code || '' }];
      for (const part of parts) {
        // A file name must not lead out of the snippet's directory
        const name = String(part.name).split(/[\\/]+/).filter(s => s && s !== '.' && s !== '..').join('/');
        entries.push({ path: folder + '/' + (name || 'file'), text: part.content ?? '' });
      }
    }
    const url = URL.createObjectURL(makeZip(entries));
    const a   = Object.assign(document.createElement('a'), { href: url, download: zipName });
    document.body.appendChild(a); a.click(); document.body.removeChild(a);
    setTimeout(() => URL.revokeObjectURL(url), 500);
  }

  // Name for the zip of one snippet: the last part of its address
  async function zipNameFor(file) {
    const address = (await addressOf(file)) || file.replace(/\.json$/, '');
    return address.split('/').pop() + '.zip';
  }

  // A button that downloads when clicked, for the pages. `files` and
  // `zipName` may be functions, for what is only known at the click.
  function downloadButton(label, files, zipName) {
    const button = document.createElement('button');
    button.type = 'button';
    button.className = 'dl-btn';
    button.textContent = label;
    button.addEventListener('click', async () => {
      button.disabled = true;
      try {
        await downloadSnippets(typeof files === 'function' ? files() : files,
                               typeof zipName === 'function' ? await zipName() : zipName);
        button.textContent = label;
      } catch (e) {
        button.textContent = '⚠ Download failed: ' + e.message;
      }
      button.disabled = false;
    });
    return button;
  }

  window.PySnippets = {
    loadIndex, srcFor, fileOf, addressFromQuery, resolve, addressOf,
    viewerUrl, linkTo, shareUrl,
    makeZip, downloadSnippets, zipNameFor, downloadButton,
  };
})();
