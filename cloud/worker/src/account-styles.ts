export const professionalAccountStyles = `:root {
  color-scheme: light;
  --paper: #f5f1e8;
  --surface: #fffdf8;
  --ink: #171715;
  --body: #3d3a35;
  --muted: #6a665f;
  --line: #d8d1c5;
  --accent: #9b3f2c;
  --display: Georgia, "Times New Roman", serif;
  --text: Georgia, "Times New Roman", serif;
  --mono: ui-monospace, SFMono-Regular, Consolas, "Liberation Mono", monospace;
  font-family: var(--text);
}

* { box-sizing: border-box; }
.sr-only { position: absolute; width: 1px; height: 1px; padding: 0; margin: -1px; overflow: hidden; clip: rect(0, 0, 0, 0); white-space: nowrap; border: 0; }
html { min-width: 320px; background: var(--paper); }
body {
  min-height: 100vh;
  margin: 0;
  display: grid;
  grid-template-rows: auto 1fr auto;
  color: var(--ink);
  background: var(--paper);
  font-family: var(--text);
  font-size: 1rem;
  line-height: 1.55;
  -webkit-font-smoothing: antialiased;
  text-rendering: optimizeLegibility;
}
a { color: inherit; }
button, a { -webkit-tap-highlight-color: transparent; }
button { font: inherit; }

.brand-header,
.account-footer {
  width: min(100% - 40px, 1120px);
  margin-inline: auto;
}
.brand-header { padding: 24px 0; border-bottom: 1px solid var(--line); }
.brand-lockup {
  display: inline-flex;
  align-items: center;
  gap: 11px;
  text-decoration: none;
}
.brand-mark {
  width: 42px;
  height: 42px;
  border: 1px solid var(--line);
  border-radius: 12px;
  object-fit: cover;
}
.wordmark { font-family: var(--mono); font-size: .78rem; font-weight: 700; letter-spacing: .28em; text-transform: uppercase; }

.account-main {
  width: 100%;
  display: grid;
  place-items: center;
  padding: clamp(48px, 9vw, 110px) 16px;
}
.account-surface {
  width: min(100%, 480px);
  padding: clamp(30px, 7vw, 52px);
  border: 1px solid var(--line);
  background: var(--surface);
  box-shadow: 0 22px 60px rgba(23, 23, 21, .08);
}
.account-surface-wide { width: min(100%, 720px); }
.account-surface h1,
.account-surface h2 {
  max-width: 12ch;
  margin: 0;
  font-family: var(--display);
  font-size: clamp(2.55rem, 6vw, 3.7rem);
  font-weight: 600;
  letter-spacing: -.015em;
  line-height: 1.02;
}
.account-surface-wide h2 { max-width: none; }
.surface-kicker {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 24px;
  color: var(--muted);
  font-family: var(--mono);
  font-size: .68rem;
  font-weight: 600;
  letter-spacing: .16em;
  text-transform: uppercase;
}
.state-badge { color: var(--ink); }
.state-badge[data-tone="attention"] { color: var(--accent); }
.state-badge[data-tone="ended"] { color: var(--muted); }
.lede { max-width: 62ch; margin: 18px 0 0; color: var(--body); font-size: 1.03rem; line-height: 1.6; }

.provider-actions { display: grid; gap: 12px; margin-top: 32px; }
.provider-button {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 11px;
  min-height: 50px;
  padding: 12px 18px;
  border: 1px solid var(--ink);
  font-family: var(--mono);
  font-size: .76rem;
  font-weight: 600;
  letter-spacing: .06em;
  text-decoration: none;
  transition: transform 150ms ease, box-shadow 150ms ease;
}
.provider-button svg { width: 20px; height: 20px; flex: none; }
.provider-google { background: var(--surface); }
.provider-github { background: var(--ink); color: #fff; }
.provider-button:hover { transform: translateY(-2px); box-shadow: 0 8px 20px rgba(23, 23, 21, .1); }
.provider-button:focus-visible,
.primary-action:focus-visible,
.secondary-action:focus-visible,
.brand-lockup:focus-visible,
.account-footer a:focus-visible { outline: 3px solid var(--accent); outline-offset: 4px; }
.provider-divider { display: grid; grid-template-columns: 1fr auto 1fr; gap: 12px; align-items: center; color: var(--muted); font-size: .78rem; text-align: center; }
.provider-divider::before, .provider-divider::after { content: ""; height: 1px; background: var(--line); }
.identity-note, .fine-print, .action-status {
  color: var(--muted);
  font-size: .86rem;
  line-height: 1.55;
}
.identity-note { margin: 24px 0 0; text-align: center; }

.plan-facts { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); margin: 26px 0 0; border-block: 1px solid var(--line); }
.plan-fact { padding: 16px 0; }
.plan-fact + .plan-fact { padding-left: 20px; border-left: 1px solid var(--line); }
.plan-fact dt { color: var(--muted); font-family: var(--mono); font-size: .66rem; font-weight: 600; letter-spacing: .13em; text-transform: uppercase; }
.plan-fact dd { margin: 7px 0 0; font-family: var(--mono); font-size: .88rem; font-weight: 600; line-height: 1.4; }
.action-stack { display: grid; gap: 10px; margin-top: 26px; }
.primary-action, .secondary-action {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-height: 46px;
  padding: 11px 16px;
  border: 1px solid var(--ink);
  cursor: pointer;
  font-family: var(--mono);
  font-size: .72rem;
  font-weight: 600;
  letter-spacing: .06em;
  line-height: 1.35;
  text-transform: uppercase;
  text-decoration: none;
}
.primary-action { background: var(--ink); color: #fff; }
.secondary-action { background: transparent; color: var(--ink); }
.primary-action:disabled, .secondary-action:disabled { cursor: wait; opacity: .62; }
.plan-choice { display: grid; grid-template-columns: 1fr auto; align-items: center; gap: 14px; padding: 15px; border: 1px solid var(--line); }
.plan-choice strong, .plan-choice span { display: block; }
.plan-choice span { margin-top: 4px; color: var(--muted); font-size: .82rem; }
.action-status { min-height: 1.4em; margin: 14px 0 0; }

.continuity-root {
  display: grid;
  gap: 22px;
  margin-top: 32px;
  padding-top: 30px;
  border-top: 1px solid var(--line);
}
.continuity-heading {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 22px;
}
.continuity-heading h3,
.danger-zone h3 { margin: 5px 0 0; font-family: var(--display); font-size: 1.65rem; font-weight: 600; letter-spacing: -.01em; line-height: 1.12; }
.danger-zone h3 { color: var(--body); font-size: 1.45rem; }
.section-label { margin: 0; color: var(--muted); font-family: var(--mono); font-size: .65rem; font-weight: 600; letter-spacing: .16em; text-transform: uppercase; }
.continuity-copy { max-width: 60ch; margin: 7px 0 0; color: var(--body); font-size: .92rem; line-height: 1.55; }
.pairing-result {
  padding: 18px;
  border: 1px solid var(--ink);
  background: var(--paper);
}
.pairing-result[hidden] { display: none; }
.pairing-code { display: block; margin: 10px 0; overflow-wrap: anywhere; font: 600 1rem/1.45 var(--mono); letter-spacing: .03em; }
.device-list { display: grid; border-top: 1px solid var(--line); }
.device-row {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  align-items: center;
  gap: 20px;
  padding: 17px 0;
  border-bottom: 1px solid var(--line);
}
.device-row strong, .device-row span { display: block; }
.device-meta { margin-top: 5px; color: var(--muted); font-family: var(--mono); font-size: .72rem; line-height: 1.45; }
.device-empty { margin: 0; padding: 16px 0; color: var(--muted); font-size: .9rem; }
.compact-action { min-height: 38px; padding: 8px 12px; font-size: .66rem; }
.continuity-links { display: flex; flex-wrap: wrap; gap: 12px; }
.danger-zone { padding: 22px; border: 1px solid #b99a90; background: #fff9f5; }
.danger-form { display: grid; gap: 12px; margin-top: 18px; }
.danger-form label { color: var(--body); font-size: .86rem; line-height: 1.5; }
.danger-form label code { font-family: var(--mono); font-size: .78rem; }
.danger-form input { width: 100%; min-height: 44px; padding: 10px 12px; border: 1px solid var(--line); border-radius: 0; background: var(--surface); color: var(--ink); font-family: var(--mono); font-size: .82rem; }
.danger-form input:focus-visible { outline: 3px solid var(--accent); outline-offset: 2px; }
.danger-form button:not(:disabled) { border-color: var(--accent); color: var(--accent); }

.account-footer {
  display: flex;
  flex-wrap: wrap;
  gap: 22px;
  padding: 24px 0 38px;
  border-top: 1px solid var(--line);
  color: var(--muted);
  font-family: var(--mono);
  font-size: .7rem;
  letter-spacing: .04em;
}
.account-footer a { text-underline-offset: 3px; }

@media (max-width: 520px) {
  .brand-header, .account-footer { width: min(100% - 32px, 1120px); }
  .account-main { padding: 38px 16px 52px; }
  .account-surface { padding: 30px 22px 34px; }
  .plan-facts { grid-template-columns: 1fr; }
  .plan-fact + .plan-fact { padding-left: 0; border-top: 1px solid var(--line); border-left: 0; }
  .plan-choice { grid-template-columns: 1fr; }
  .plan-choice button { width: 100%; }
  .continuity-heading, .device-row { align-items: stretch; grid-template-columns: 1fr; }
  .continuity-heading { display: grid; }
  .continuity-heading button, .device-row button, .continuity-links a { width: 100%; }
}

@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after { scroll-behavior: auto !important; transition: none !important; }
}`;
