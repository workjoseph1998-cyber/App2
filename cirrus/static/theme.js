// Resolve the saved appearance before the page is painted.
try {
  document.documentElement.dataset.theme = localStorage.getItem('cirrus-theme') || 'light';
} catch (_) {}
