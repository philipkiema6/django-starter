// Dark mode toggle: persists the chosen DaisyUI theme ("light"/"dark") to localStorage and
// swaps the `data-theme` attribute on <html>. See templates/web/base.html for the inline
// pre-paint script that applies the stored theme before first render (avoids a flash).
const STORAGE_KEY = 'theme';

function get() {
  return localStorage.getItem(STORAGE_KEY) || 'light';
}

function set(theme) {
  localStorage.setItem(STORAGE_KEY, theme);
  // data-theme drives DaisyUI's color palette; the "dark" class drives Tailwind's own
  // `dark:` variant utilities (tailwind.config.js uses the "class" darkMode strategy).
  document.documentElement.setAttribute('data-theme', theme);
  document.documentElement.classList.toggle('dark', theme === 'dark');
}

function toggle() {
  set(get() === 'dark' ? 'light' : 'dark');
}

if (typeof window.SiteJS === 'undefined') {
  window.SiteJS = {};
}

window.SiteJS.theme = { get, set, toggle };
