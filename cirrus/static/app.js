try { if (localStorage.getItem('cirrus-theme') === 'dark') document.documentElement.dataset.theme = 'dark'; } catch (_) {}
document.getElementById('theme-toggle')?.addEventListener('click', () => {
  const theme = document.documentElement.dataset.theme === 'dark' ? 'light' : 'dark';
  document.documentElement.dataset.theme = theme;
  try { localStorage.setItem('cirrus-theme', theme); } catch (_) {}
});
document.getElementById('print-label')?.addEventListener('click', () => window.print());
for (const link of document.querySelectorAll('nav a')) if (link.getAttribute('href') === location.pathname) link.classList.add('active');
