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

  window.PySnippets = {
    loadIndex, srcFor, fileOf, addressFromQuery, resolve, addressOf,
    viewerUrl, linkTo, shareUrl,
  };
})();
