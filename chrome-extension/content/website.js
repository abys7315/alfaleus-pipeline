/**
 * Alfaleus Lead Intelligence — Generic Website Content Script
 * Extracts company metadata from any non-LinkedIn webpage.
 */

(function () {
  'use strict';

  // ─── Helpers ───────────────────────────────────────────────────────────────

  function getMeta(property, attr = 'content') {
    const el =
      document.querySelector(`meta[property="${property}"]`) ||
      document.querySelector(`meta[name="${property}"]`);
    return el ? (el.getAttribute(attr) || '').trim() : '';
  }

  function getText(el) {
    if (!el) return '';
    return (el.innerText || el.textContent || '').trim();
  }

  // ─── Company Name Detection ────────────────────────────────────────────────

  function extractCompanyName() {
    // 1. og:site_name — most reliable signal
    const ogSiteName = getMeta('og:site_name');
    if (ogSiteName && ogSiteName.length > 0) return ogSiteName;

    // 2. application-name meta tag
    const appName = getMeta('application-name');
    if (appName && appName.length > 0) return appName;

    // 3. Twitter site name
    const twitterSite = getMeta('twitter:site');
    if (twitterSite && twitterSite.length > 0) return twitterSite.replace('@', '');

    // 4. Title tag — take first segment before common separators
    const title = (document.title || '').trim();
    if (title) {
      const segments = title.split(/\s*[\|\-—–·•]\s*/);
      // Prefer the shortest segment that's not a generic word
      const genericWords = ['home', 'welcome', 'index', 'main', 'official'];
      const bestSegment = segments.find(
        (s) => s.length > 1 && !genericWords.includes(s.toLowerCase())
      );
      if (bestSegment) return bestSegment.trim();
    }

    // 5. First H1 if it reads like a company/brand name (≤ 6 words)
    const h1 = document.querySelector('h1');
    if (h1) {
      const h1Text = getText(h1);
      if (h1Text && h1Text.split(/\s+/).length <= 6) return h1Text;
    }

    // 6. Derive from hostname
    const hostname = location.hostname.replace(/^www\./, '');
    const domainName = hostname.split('.')[0];
    // Capitalise first letter
    return domainName.charAt(0).toUpperCase() + domainName.slice(1);
  }

  // ─── Description / About ──────────────────────────────────────────────────

  function extractDescription() {
    const ogDesc = getMeta('og:description');
    if (ogDesc) return ogDesc;

    const metaDesc = getMeta('description');
    if (metaDesc) return metaDesc;

    const twitterDesc = getMeta('twitter:description');
    if (twitterDesc) return twitterDesc;

    return '';
  }

  // ─── LinkedIn URL hunting ─────────────────────────────────────────────────

  function findLinkedInUrl() {
    const links = document.querySelectorAll('a[href*="linkedin.com/company"], a[href*="linkedin.com/in/"]');
    for (const link of links) {
      const href = link.getAttribute('href') || '';
      if (href.includes('linkedin.com')) return href.split('?')[0];
    }
    return '';
  }

  // ─── Social / contact signals ─────────────────────────────────────────────

  function findTwitterHandle() {
    const twitterMeta = getMeta('twitter:site') || getMeta('twitter:creator');
    if (twitterMeta) return twitterMeta;

    const twitterLink = document.querySelector('a[href*="twitter.com/"], a[href*="x.com/"]');
    if (twitterLink) {
      const href = twitterLink.getAttribute('href') || '';
      const match = href.match(/(?:twitter|x)\.com\/(@?\w+)/);
      if (match) return match[1];
    }
    return '';
  }

  // ─── Main Extraction ──────────────────────────────────────────────────────

  function extractWebsiteData() {
    const company = extractCompanyName();
    const description = extractDescription();
    const linkedin_url = findLinkedInUrl();
    const twitter = findTwitterHandle();
    const domain = location.hostname.replace(/^www\./, '');

    const data = {
      company,
      description,
      url: location.href,
      domain,
      linkedin_url,
      twitter,
      page_type: 'website',
      source: 'website',
      page_title: (document.title || '').trim(),
    };

    // Store for popup retrieval via scripting.executeScript
    try {
      sessionStorage.setItem('alfaleus_extracted', JSON.stringify(data));
    } catch (e) {
      // Private mode / quota — ignore
    }

    // Notify background / popup
    chrome.runtime.sendMessage({ type: 'WEBSITE_DATA', data }, () => {
      if (chrome.runtime.lastError) { /* suppress "no receiver" error */ }
    });
  }

  // ─── Run ──────────────────────────────────────────────────────────────────

  // Some sites load meta tags lazily; run after a brief delay too
  extractWebsiteData();
  setTimeout(extractWebsiteData, 1500);
})();
