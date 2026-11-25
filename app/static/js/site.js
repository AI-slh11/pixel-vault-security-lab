document.addEventListener('DOMContentLoaded', () => {
  const button = document.querySelector('.mobile-menu');
  if (button) button.addEventListener('click', () => {
    document.body.classList.toggle('nav-open');
    button.setAttribute('aria-expanded', document.body.classList.contains('nav-open') ? 'true' : 'false');
  });
});
