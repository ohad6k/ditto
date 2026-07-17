# Emulo Continuity Onboarding Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Turn Emulo Pro's verified encrypted-continuity primitives into a safe first-device, recovery, pairing, push/pull, conflict, device-management, export, and deletion customer workflow without enabling checkout.

**Architecture:** The Worker account page creates browser-authenticated one-time grants and manages safe device metadata. The Python companion owns every private key, master key, recovery secret, decrypted generation, and device bearer token; it communicates with the Worker only through exact HTTPS origins and structured bounded JSON. The existing local engine remains usable without the Pro extra or an entitlement.

**Tech Stack:** Python 3.11, `cryptography`, `argparse`, `urllib`, Cloudflare Workers, TypeScript, D1, Vitest, pytest.

---

## File map

- Create `emulo_autopilot/continuity_onboarding.py`: versioned recovery-kit/credential files and first-device/recovery/connect orchestration.
- Modify `emulo_autopilot/continuity_crypto.py`: derive the public key from validated private device material.
- Modify `emulo_autopilot/continuity.py`: secure pairing completion and reusable strict JSON transport behavior.
- Modify `emulo_autopilot/cli.py`: lazy-loaded customer commands and hidden secret input.
- Create `tests/test_continuity_onboarding.py`: local setup/recovery/connect and secret-safety proof.
- Modify `tests/test_continuity.py`: pairing transport rejection/acceptance tests.
- Modify `tests/test_autopilot_cli.py`: command contract, lazy dependency, and output-safety tests.
- Modify `tests/test_continuity_two_device.py`: CLI-level synthetic first/second-device proof.
- Modify `cloud/worker/src/account-ui.ts`: active-account device, export, and deletion interface.
- Modify `cloud/worker/test/account-ui.test.ts`: active-only controls, safe copy, and secret/provider-ID absence.
- Modify `.viberaven/production-context.md` and the continuity release evidence after fresh verification.

### Task 1: Secure local setup and recovery files

**Files:**
- Create: `tests/test_continuity_onboarding.py`
- Create: `emulo_autopilot/continuity_onboarding.py`
- Modify: `emulo_autopilot/continuity_crypto.py`

- [ ] **Step 1: Write the failing setup and recovery tests**

```python
def test_initialize_writes_private_keys_and_portable_kit_without_secret(tmp_path):
    result = initialize_continuity(tmp_path)
    assert result["schema_version"] == "emulo.continuity-setup/v1"
    assert result["recovery_secret"] not in (tmp_path / "continuity" / "recovery-kit.json").read_text()
    assert not (tmp_path / "continuity" / "device.json").exists()

def test_recover_restores_master_key_with_a_fresh_device_key(tmp_path):
    first = initialize_continuity(tmp_path / "first")
    recovered = recover_continuity(
        tmp_path / "second",
        tmp_path / "first" / "continuity" / "recovery-kit.json",
        first["recovery_secret"],
    )
    assert read_private_material(first["private_material_path"])[1] == read_private_material(recovered["private_material_path"])[1]
    assert read_private_material(first["private_material_path"])[0] != read_private_material(recovered["private_material_path"])[0]
```

- [ ] **Step 2: Run the tests and confirm the missing-module/API failure**

Run: `python -m pytest tests/test_continuity_onboarding.py -q`

Expected: FAIL because `emulo_autopilot.continuity_onboarding` does not exist.

- [ ] **Step 3: Implement exact schemas, atomic files, and no-overwrite behavior**

```python
RECOVERY_KIT_SCHEMA = "emulo.continuity-recovery-kit/v1"
CREDENTIAL_SCHEMA = "emulo.continuity-device-credential/v1"

def initialize_continuity(home):
    private_key, public_key = generate_device_key_pair()
    master_key = generate_master_key()
    recovery_secret = generate_recovery_secret()
    kit = {
        "schema_version": RECOVERY_KIT_SCHEMA,
        "wrapped_master_key": wrap_master_key_for_recovery(master_key, recovery_secret),
    }
    # Refuse existing targets; atomically write keys and portable kit.
    return {
        "schema_version": SETUP_SCHEMA,
        "recovery_secret": recovery_secret,
        "private_material_path": str(_private_path(home)),
        "recovery_kit_path": str(_recovery_kit_path(home)),
        "device_public_key": encode_public_key(public_key),
    }
```

Add `device_public_key(device_private_key)` to `continuity_crypto.py` and use the existing strict X25519 encoding.

- [ ] **Step 4: Add wrong-secret, symlink, malformed-kit, and overwrite-refusal tests**

Run: `python -m pytest tests/test_continuity_onboarding.py -q`

Expected: PASS with every recovery failure leaving existing files unchanged.

- [ ] **Step 5: Commit the local onboarding unit**

```powershell
git add emulo_autopilot/continuity_crypto.py emulo_autopilot/continuity_onboarding.py tests/test_continuity_onboarding.py
git commit -m "feat: add secure continuity onboarding files"
```

### Task 2: Secure pairing completion and credential persistence

**Files:**
- Modify: `tests/test_continuity.py`
- Modify: `tests/test_continuity_onboarding.py`
- Modify: `emulo_autopilot/continuity.py`
- Modify: `emulo_autopilot/continuity_onboarding.py`

- [ ] **Step 1: Write failing transport tests**

```python
def test_complete_pairing_posts_bounded_json_without_redirect_or_url_secret(fake_https):
    result = complete_pairing("https://emulo.example", body, opener=fake_https)
    assert result == {"deviceId": DEVICE_ID, "deviceToken": DEVICE_TOKEN}
    assert fake_https.request.full_url == "https://emulo.example/v1/devices/pair/complete"
    assert "Authorization" not in fake_https.request.headers

@pytest.mark.parametrize("origin", ["http://emulo.example", "https://u:p@emulo.example", "https://emulo.example/path", "https://emulo.example?x=1"])
def test_complete_pairing_rejects_non_origin_urls(origin):
    with pytest.raises(ValueError, match="HTTPS origin"):
        complete_pairing(origin, body)
```

- [ ] **Step 2: Run the focused tests and observe the missing function failure**

Run: `python -m pytest tests/test_continuity.py tests/test_continuity_onboarding.py -q`

Expected: FAIL because `complete_pairing` and credential persistence are absent.

- [ ] **Step 3: Implement pairing and safe credential storage**

```python
def complete_pairing(base_url, payload, timeout=15, opener=None):
    origin = _https_origin(base_url)
    return _json_request(opener or _strict_opener(), origin, "POST", "/v1/devices/pair/complete", payload, timeout)

def connect_continuity(home, base_url, pairing_code, label, client_version):
    private_key, master_key = read_private_material(_private_path(home))
    public_key = device_public_key(private_key)
    wrapped = wrap_master_key_for_device(master_key, public_key)
    paired = complete_pairing(base_url, {
        "pairingCode": pairing_code,
        "label": label,
        "keyAgreementPublicKey": encode_public_key(public_key),
        "wrappedMasterKey": wrapped,
        "clientVersion": client_version,
    })
    _write_private_json(_credential_path(home), validated_credential)
    return {"schema_version": CONNECT_SCHEMA, "device_id": paired["deviceId"], "server": base_url}
```

The returned device token is never included in the safe result.

- [ ] **Step 4: Verify malformed JSON, redirect, invalid ID/token, and existing-credential rejection**

Run: `python -m pytest tests/test_continuity.py tests/test_continuity_onboarding.py -q`

Expected: PASS.

- [ ] **Step 5: Commit the pairing unit**

```powershell
git add emulo_autopilot/continuity.py emulo_autopilot/continuity_onboarding.py tests/test_continuity.py tests/test_continuity_onboarding.py
git commit -m "feat: connect continuity devices securely"
```

### Task 3: Customer continuity CLI

**Files:**
- Modify: `tests/test_autopilot_cli.py`
- Modify: `emulo_autopilot/cli.py`

- [ ] **Step 1: Write failing command-contract and lazy-import tests**

```python
def test_continuity_recover_reads_secret_from_hidden_prompt(tmp_path, capsys):
    main(["--emulo-home", str(tmp_path), "continuity-recover", str(kit)], secret_reader=lambda _: RECOVERY_SECRET)
    captured = capsys.readouterr()
    assert RECOVERY_SECRET not in captured.out + captured.err

def test_base_status_does_not_import_optional_continuity(monkeypatch, tmp_path):
    monkeypatch.setitem(sys.modules, "cryptography", None)
    result = execute(build_parser().parse_args(["--emulo-home", str(tmp_path), "status"]))
    assert result["schema_version"] == "emulo.autopilot-status/v1"
```

Add focused tests for init, connect hidden-code prompt, local/offline status, push, retry, pull activation, and conflict JSON.

- [ ] **Step 2: Run and confirm parser/keyword failures**

Run: `python -m pytest tests/test_autopilot_cli.py -q`

Expected: FAIL because the commands and `secret_reader` injection do not exist.

- [ ] **Step 3: Add lazy-loaded commands**

```python
def main(argv=None, clock=time.time, secret_reader=getpass.getpass):
    args = build_parser().parse_args(argv)
    result = execute(args, clock=clock, secret_reader=secret_reader)

if args.command == "continuity-pull":
    from .continuity_onboarding import load_connected_transport
    from .continuity import pull_remote_head
    private_key, master_key, transport = load_connected_transport(home)
    return pull_remote_head(store, master_key, transport)
```

Use hidden prompts for recovery secrets and pairing codes, never bearer tokens. Keep structured safe JSON and current error handling.

- [ ] **Step 4: Run CLI and full focused continuity tests**

Run: `python -m pytest tests/test_autopilot_cli.py tests/test_continuity_onboarding.py tests/test_continuity.py -q`

Expected: PASS with no recovery/token marker in captured output.

- [ ] **Step 5: Commit the CLI unit**

```powershell
git add emulo_autopilot/cli.py tests/test_autopilot_cli.py
git commit -m "feat: expose continuity customer workflow"
```

### Task 4: Active-account device controls

**Files:**
- Modify: `cloud/worker/test/account-ui.test.ts`
- Modify: `cloud/worker/src/account-ui.ts`

- [ ] **Step 1: Write failing active-only UI tests**

```typescript
it("offers pairing and device controls only to active Pro accounts", async () => {
  const active = await renderAccountPage(activeStatus());
  const inactive = await renderAccountPage(noneStatus());
  expect(active).toContain("data-create-pairing-code");
  expect(active).toContain("data-device-list");
  expect(active).toContain("delete-cloud-continuity");
  expect(inactive).not.toContain("data-create-pairing-code");
});

it("never embeds device credentials or wrapped keys", async () => {
  const html = await renderAccountPage(activeStatus());
  expect(html).not.toMatch(/deviceToken|wrappedMasterKey|Authorization: Bearer/);
});
```

- [ ] **Step 2: Run and observe the missing-controls failures**

Run from `cloud/worker`: `npm test -- account-ui.test.ts`

Expected: FAIL on missing data attributes and confirmation copy.

- [ ] **Step 3: Implement the device and danger sections**

```html
<section class="account-section" aria-labelledby="devices-title">
  <div class="section-heading"><div><p class="eyebrow">DEVICES</p><h3 id="devices-title">Keep your work in step</h3></div><button data-create-pairing-code>Create pairing code</button></div>
  <div data-pairing-result hidden aria-live="polite"></div>
  <div data-device-list aria-live="polite"></div>
</section>
```

Add same-origin handlers for `POST /v1/devices/pair/start`, `GET /v1/devices`, per-device `DELETE`, `GET /v1/continuity/export`, and exact-confirmation `DELETE /v1/continuity`. Render only allowlisted fields with `textContent`, never `innerHTML` for API data.

- [ ] **Step 4: Run focused account/auth/continuity Worker tests and typecheck**

Run: `npm test -- account-ui.test.ts device-auth.test.ts continuity-routes.test.ts continuity-lifecycle.test.ts; npm run typecheck`

Expected: all selected tests and typecheck pass.

- [ ] **Step 5: Commit the account unit**

```powershell
git add cloud/worker/src/account-ui.ts cloud/worker/test/account-ui.test.ts
git commit -m "feat: add continuity account controls"
```

### Task 5: CLI-level two-device proof and release evidence

**Files:**
- Modify: `tests/test_continuity_two_device.py`
- Modify: `.viberaven/production-context.md`
- Modify: `docs/superpowers/plans/2026-07-17-emulo-pro-continuity-release-evidence.md`

- [ ] **Step 1: Write a failing CLI-level synthetic proof**

```python
def test_cli_first_device_to_recovered_second_device_preserves_exact_artifacts(tmp_path, fake_server):
    first = run_cli(tmp_path / "a", "continuity-init")
    run_cli(tmp_path / "a", "continuity-connect", input_secret=fake_server.code)
    run_cli(tmp_path / "a", "continuity-push")
    run_cli(tmp_path / "b", "continuity-recover", str(first.kit), input_secret=first.recovery_secret)
    run_cli(tmp_path / "b", "continuity-connect", input_secret=fake_server.second_code)
    pulled = run_cli(tmp_path / "b", "continuity-pull")
    assert pulled["status"] == "activated"
    assert (tmp_path / "b" / "autopilot" / "active" / "work.md").read_bytes() == SYNTHETIC_UNICODE_CRLF
```

- [ ] **Step 2: Run the proof and fix only onboarding integration gaps**

Run: `python -m pytest tests/test_continuity_two_device.py -q`

Expected: PASS after the smallest integration corrections.

- [ ] **Step 3: Run fresh complete verification**

Run the full Python suite, full Worker suite, typecheck, production config guards, npm production audit, clean `.[pro]` pip check, Wrangler production dry run, known-marker scans, and desktop/390-pixel authenticated browser QA. Record exact counts and failures; do not reuse earlier evidence.

- [ ] **Step 4: Update production memory and release evidence**

Record repository proof separately from unknown provider state. Keep Google production activation, D1 application/deploy, Polar lifecycle, and real two-device production proof open. Confirm `PAID_CHECKOUT_ENABLED=false`.

- [ ] **Step 5: Commit verified evidence**

```powershell
git add tests/test_continuity_two_device.py .viberaven/production-context.md docs/superpowers/plans/2026-07-17-emulo-pro-continuity-release-evidence.md
git commit -m "test: prove continuity customer onboarding"
```

No push, deploy, migration application, provider mutation, or checkout activation is part of this plan.
