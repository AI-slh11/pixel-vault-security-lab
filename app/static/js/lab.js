(() => {
  const workspace = document.querySelector('.lab-workspace');
  if (!workspace) return;
  const mode = workspace.dataset.mode === 'secure' ? 'secure' : 'vulnerable';
  const state = { scenario: 'member' };
  const definitions = {
    member: { type: 'MEMBER FEATURE', title: 'Player library response', copy: 'A sample member-only library response. Use the demo player account to compare the protected route.', paths: { vulnerable: '/lab/vulnerable/member-download', secure: '/lab/secure/member-download' } },
    admin: { type: 'ADMIN FEATURE', title: 'Catalog overview response', copy: 'A fictional catalog summary reserved for administrator practice. Compare the route responses with each demo role.', paths: { vulnerable: '/lab/vulnerable/admin-report', secure: '/lab/secure/admin-report' } },
  };
  const path = document.querySelector('#lab-path');
  const routeLabel = document.querySelector('#lab-mode-label');
  const status = document.querySelector('#lab-status');
  const output = document.querySelector('#lab-output');
  const takeaway = document.querySelector('#lab-takeaway');
  function update() {
    const item = definitions[state.scenario];
    path.textContent = item.paths[mode];
    document.querySelector('#lab-scenario-type').textContent = item.type;
    document.querySelector('#lab-scenario-title').textContent = item.title;
    document.querySelector('#lab-scenario-copy').textContent = item.copy;
    routeLabel.textContent = mode === 'vulnerable' ? 'PRACTICE ROUTE' : 'PROTECTED ROUTE';
    status.textContent = '';
    output.innerHTML = '<span class="lab-placeholder">Your response will appear here.</span>';
    takeaway.textContent = 'Use only the included demo accounts. The local test database contains no real player information.';
  }
  document.querySelectorAll('.lab-choice').forEach((button) => button.addEventListener('click', () => {
    state.scenario = button.dataset.scenario;
    document.querySelectorAll('.lab-choice').forEach((choice) => choice.classList.toggle('active', choice === button));
    update();
  }));
  document.querySelector('#lab-run').addEventListener('click', async (event) => {
    const button = event.currentTarget;
    button.disabled = true;
    button.innerHTML = 'Sending request… <span>◌</span>';
    status.textContent = '';
    try {
      const response = await fetch(definitions[state.scenario].paths[mode], { headers: { Accept: 'application/json' }, credentials: 'same-origin', cache: 'no-store' });
      const body = await response.json();
      status.textContent = `${response.status} ${response.statusText.toUpperCase()}`;
      status.className = response.ok ? 'status-ok' : 'status-denied';
      output.textContent = JSON.stringify(body, null, 2);
      takeaway.textContent = response.ok ? 'The route returned a response for this local demo session. Compare the identity and role represented by the visitor with the intended feature access.' : 'The protected route denied this request. Sign in with the appropriate demo role and compare again.';
    } catch {
      status.textContent = 'NETWORK ERROR';
      output.textContent = JSON.stringify({ error: 'The local server did not return a response.' }, null, 2);
      takeaway.textContent = 'Confirm the app is running locally, then retry the request.';
    } finally {
      button.disabled = false;
      button.innerHTML = 'Send request <span>→</span>';
    }
  });
  update();
})();
