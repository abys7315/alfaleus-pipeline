import Papa from 'papaparse';

export function validateCSV(file) {
  return new Promise((resolve) => {
    if (!file) return resolve({ valid: false, errors: ['No file selected'], preview: [] });
    if (!file.name.endsWith('.csv')) {
      return resolve({ valid: false, errors: ['File must be a .csv file'], preview: [] });
    }
    if (file.size > 10 * 1024 * 1024) {
      return resolve({ valid: false, errors: ['File must be under 10MB'], preview: [] });
    }

    Papa.parse(file, {
      header: true,
      skipEmptyLines: true,
      preview: 10,
      complete: (result) => {
        const errors = [];
        if (!result.data || result.data.length === 0) {
          errors.push('CSV is empty');
          return resolve({ valid: false, errors, preview: [] });
        }

        const headers = Object.keys(result.data[0] || {}).map(h => h.toLowerCase().trim());
        const hasName = headers.includes('name') || headers.includes('full_name');
        const hasCompany = headers.includes('company') || headers.includes('company_name');
        const hasEmail = headers.includes('email');
        const hasDomain = headers.includes('domain');

        if (!((hasName && hasCompany) || hasEmail || hasDomain)) {
          errors.push(
            'CSV must have: "name" + "company" columns, OR "email" column, OR "domain" column'
          );
        }

        if (result.errors && result.errors.length > 0) {
          result.errors.slice(0, 3).forEach(e => errors.push(`Row ${e.row}: ${e.message}`));
        }

        const preview = result.data.slice(0, 5);
        resolve({ valid: errors.length === 0, errors, preview, total: result.data.length });
      },
      error: (err) => {
        resolve({ valid: false, errors: [`Parse error: ${err.message}`], preview: [] });
      },
    });
  });
}

export function formatCSVData(rows) {
  return rows.map(row => {
    const norm = {};
    Object.entries(row).forEach(([k, v]) => { norm[k.toLowerCase().trim()] = (v || '').trim(); });
    return {
      name: norm.name || norm.full_name || null,
      email: norm.email || null,
      company: norm.company || norm.company_name || null,
      domain: norm.domain || null,
      linkedin_url: norm.linkedin_url || norm.linkedin || null,
    };
  });
}
