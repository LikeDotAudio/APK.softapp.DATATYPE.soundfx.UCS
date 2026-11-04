// Part of the APK.audio project — http://APK.audio — made by Anthony Kuzub
// MIT Licence. Free, for everyone, for ever. Full text in LICENSE at the root.
// THE ONE TABLE (ROAD-3494): a UCS category registers as APKTable 'ucs-<category>',
// drawn by js/taxonomy-table.js from a real categories/*.json on the vendored apk-table.
import { test } from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import { createRequire } from 'node:module';
const require = createRequire(import.meta.url);
const { loadApkTable, runInShim, rowsOf } = require('./apk-table-shim.cjs');
const APP = new URL('..', import.meta.url).pathname;

test('a category is APKTable ucs-<category>, one row per subcategory', () => {
  const { window, document } = loadApkTable(APP + 'vendor/apk-table/apk-table.js');
  runInShim(window, APP + 'js/taxonomy-table.js');
  const index = JSON.parse(fs.readFileSync(APP + 'categories/index.json', 'utf8'));
  const data = JSON.parse(fs.readFileSync(APP + 'categories/' + index.categories[0].file, 'utf8'));
  const t = window.ucsCategoryTable(document.createElement('div'), data);
  assert.equal(t.id, window.ucsTableId(data.category));
  assert.match(t.id, /^ucs-[a-z0-9-]+$/);
  assert.equal(window.APKTable.get(t.id), t);
  const rows = rowsOf(t);
  assert.equal(rows.length, data.subcategories.length);
  assert.equal(rows[0][1], data.subcategories[0].category_id);
});

test('index.html loads the vendored table and draws no <table> itself', () => {
  const html = fs.readFileSync(APP + 'index.html', 'utf8');
  assert.match(html, /vendor\/apk-table\/apk-table\.js/);
  assert.doesNotMatch(html, /<table|createElement\(['"]table/);
});
