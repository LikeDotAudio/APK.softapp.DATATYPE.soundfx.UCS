// Part of the APK.audio project — http://APK.audio — made by Anthony Kuzub
// MIT Licence. Free, for everyone, for ever. Full text in LICENSE at the root.
// THE ONE TABLE (ROAD-3494): each UCS category's subcategories are an APKTable
// (vendor/apk-table, held to /FrontEnd/shared by check.sh webshared), id
// 'ucs-<category>' — APKTable.get('ucs-ambience'). Read-only; every cell text.
function ucsTableId(category) {
  return 'ucs-' + String(category).toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-+|-+$/g, '');
}

function ucsRows(data) {
  return data.subcategories.map((sub) => {
    const sig = sub.acoustic_signature || {};
    return {
      subcategory: sub.subcategory,
      id: sub.category_id,
      explanation: (sub.explanation || []).join(' '),
      morphology: sig.morphology || '—',
      separability: sig.separability || '—',
      synonyms: (sub.synonyms || []).join(', '),
      haystack: [data.category, sub.subcategory, sub.category_id, ...(sub.synonyms || [])].join(' ').toLowerCase(),
    };
  });
}

function ucsCategoryTable(host, data) {
  const code = (v) => { const c = document.createElement('code'); c.textContent = v == null ? '' : String(v); return c; };
  return APKTable.create(host, {
    id: ucsTableId(data.category),
    editable: false,
    toolbar: false,   // the page's one filter box drives every category
    columns: [
      { key: 'subcategory', label: 'Subcategory' },
      { key: 'id', label: 'Id', render: code },
      { key: 'explanation', label: 'Explanation' },
      { key: 'morphology', label: 'Morphology' },
      { key: 'separability', label: 'Separability' },
      { key: 'synonyms', label: 'Synonyms', cellClass: () => 'muted' },
    ],
    rows: ucsRows(data),
  });
}
