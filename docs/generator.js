'use strict';

(() => {
  const form = document.getElementById('generator');
  const input = document.getElementById('character-url');
  const output = document.getElementById('prompt');
  const copyButton = document.getElementById('copy');
  const error = document.getElementById('error');
  const status = document.getElementById('status');

  function characterLink(value) {
    const raw = value.trim();
    if (!raw || /\s/.test(raw)) throw new Error('Enter a complete Character.AI character link.');
    let url;
    try { url = new URL(raw); }
    catch { throw new Error('Invalid link format. Copy the full link from the character chat page.'); }
    if (url.origin !== 'https://character.ai' || url.username || url.password ||
        !/^\/chat\/[A-Za-z0-9_-]+\/?$/.test(url.pathname)) {
      throw new Error('Use a link in the format https://character.ai/chat/CHARACTER_ID.');
    }
    const normalized = new URL(url.pathname.replace(/\/$/, ''), 'https://character.ai');
    const histories = url.searchParams.getAll('hist');
    if (histories.length) {
      if (histories.length !== 1 || !/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i.test(histories[0])) {
        throw new Error('Invalid hist session parameter. Copy the link from the character chat page again.');
      }
      normalized.searchParams.set('hist', histories[0]);
    }
    return normalized.href;
  }

  function reset() {
    output.value = '';
    copyButton.disabled = true;
    error.textContent = '';
    status.textContent = '';
    input.removeAttribute('aria-invalid');
  }
  input.addEventListener('input', reset);

  form.addEventListener('submit', (event) => {
    event.preventDefault();
    reset();
    try {
      const link = characterLink(input.value);
      output.value = `Clone https://github.com/jgzirzmyauxddacdA/CAITest.git into the current workspace, or reuse an existing checkout without overwriting local changes. Read SKILL.md and references/workflow.md, then set up the dependencies as described in README.md.

Use this skill to export existing chat history and character data for: ${link}

Save the Definition only if the API explicitly returns copyable: true and provides its body. Otherwise skip it; do not attempt Definition recovery or send test messages. If login or a CAPTCHA is required, let me complete it in the Chrome window opened by the script. Wait for the runner to exit, check workflow status and ZIP verification, then return delivery.zip and report any skipped or unavailable Definition.`;
      copyButton.disabled = false;
      status.textContent = 'Prompt generated. Copy and paste it into Codex to run the workflow.';
    } catch (problem) {
      error.textContent = problem.message;
      input.setAttribute('aria-invalid', 'true');
      input.focus();
    }
  });

  copyButton.addEventListener('click', async () => {
    const text = output.value;
    if (!text) return;
    try {
      if (!navigator.clipboard?.writeText) throw new Error('Clipboard unavailable');
      await navigator.clipboard.writeText(text);
      if (output.value === text) status.textContent = 'Copied. Paste the prompt into Codex.';
    } catch {
      if (output.value !== text) return;
      output.focus();
      output.select();
      let copied = false;
      try { copied = document.execCommand('copy'); } catch { /* Keep the text selected. */ }
      status.textContent = copied ? 'Copied. Paste the prompt into Codex.' : 'Prompt selected. Press Ctrl+C (Mac: Command+C) to copy.';
    }
  });
})();
