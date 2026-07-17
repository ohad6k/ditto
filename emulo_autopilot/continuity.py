import base64
import json
import re
import urllib.error
import urllib.parse
import urllib.request

from .contracts import canonical_json, validate_generation
from .continuity_crypto import decrypt_generation, encrypt_generation


BUNDLE_SCHEMA = "emulo.continuity-bundle/v1"
MAX_BUNDLE_BYTES = 192 * 1024
MAX_RESPONSE_BYTES = 280 * 1024
_GENERATION = re.compile(r"^gen_[a-f0-9]{20}$")
_DEVICE = re.compile(r"^dev_[a-f0-9]{32}$")
_TOKEN = re.compile(r"^[A-Za-z0-9_-]{43}$")
_ARTIFACT = re.compile(r"^(work|design|write|video)\.md$")


def validate_https_origin(base_url):
    parsed = urllib.parse.urlsplit(base_url)
    if (
        parsed.scheme != "https"
        or not parsed.hostname
        or parsed.username is not None
        or parsed.password is not None
        or parsed.query
        or parsed.fragment
        or parsed.path not in {"", "/"}
    ):
        raise ValueError("continuity server URL must be an HTTPS origin")
    return base_url.rstrip("/")


def _b64(value):
    return base64.urlsafe_b64encode(value).decode("ascii").rstrip("=")


def _unb64(value):
    if not isinstance(value, str) or not re.fullmatch(r"[A-Za-z0-9_-]+", value):
        raise ValueError("continuity artifact encoding is invalid")
    try:
        decoded = base64.b64decode(
            value + "=" * ((4 - len(value) % 4) % 4),
            altchars=b"-_",
            validate=True,
        )
    except (TypeError, ValueError) as exc:
        raise ValueError("continuity artifact encoding is invalid") from exc
    if _b64(decoded) != value:
        raise ValueError("continuity artifact encoding is invalid")
    return decoded


def package_generation(store, generation_id):
    generation = store.get_generation(generation_id)
    artifacts = {}
    for domain, metadata in generation["domains"].items():
        artifacts[metadata["artifact"]] = _b64(
            store.read_domain(generation_id, domain).encode("utf-8")
        )
    payload = (
        canonical_json(
            {
                "schema_version": BUNDLE_SCHEMA,
                "generation": generation,
                "artifacts": artifacts,
            }
        )
        + "\n"
    ).encode("utf-8")
    if len(payload) > MAX_BUNDLE_BYTES:
        raise ValueError("continuity bundle is too large")
    return payload


def unpack_generation(payload):
    if not isinstance(payload, bytes) or len(payload) > MAX_BUNDLE_BYTES:
        raise ValueError("continuity bundle is invalid")
    try:
        value = json.loads(payload.decode("utf-8", errors="strict"))
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError("continuity bundle is invalid") from exc
    if not isinstance(value, dict) or set(value) != {
        "schema_version",
        "generation",
        "artifacts",
    } or value["schema_version"] != BUNDLE_SCHEMA:
        raise ValueError("continuity bundle is invalid")
    generation = validate_generation(value["generation"])
    encoded = value["artifacts"]
    if not isinstance(encoded, dict):
        raise ValueError("continuity artifacts are invalid")
    expected = {
        metadata["artifact"] for metadata in generation["domains"].values()
    }
    if set(encoded) != expected or any(not _ARTIFACT.fullmatch(name) for name in encoded):
        raise ValueError("continuity artifacts are invalid")
    artifacts = {name: _unb64(content) for name, content in encoded.items()}
    for artifact in artifacts.values():
        artifact.decode("utf-8", errors="strict")
    return generation, artifacts


def _envelope(store, master_key, device_id, generation_id):
    existing = store.get_continuity_envelope(generation_id)
    if existing is not None:
        return existing
    generation = store.get_generation(generation_id)
    envelope = encrypt_generation(
        master_key,
        generation_id=generation_id,
        parent_generation_id=generation["parent_generation_id"],
        author_device_id=device_id,
        created_at=generation["created_at"],
        plaintext=package_generation(store, generation_id),
    )
    store.put_continuity_envelope(generation_id, envelope)
    return envelope


def push_active(store, master_key, device_id, transport, generation_id=None):
    if not isinstance(device_id, str) or not _DEVICE.fullmatch(device_id):
        raise ValueError("device_id is invalid")
    if generation_id is None:
        head = store.get_head()
        if head is None:
            raise ValueError("there is no active generation")
        generation_id = head["generation_id"]
    envelope = _envelope(store, master_key, device_id, generation_id)
    try:
        result = transport.upload(envelope)
    except Exception:
        store.put_continuity_pending(generation_id, envelope)
        raise
    store.delete_continuity_pending(generation_id)
    return result


def retry_pending(store, transport):
    uploaded = 0
    for generation_id in store.list_continuity_pending():
        envelope = store.get_continuity_pending(generation_id)
        transport.upload(envelope)
        store.delete_continuity_pending(generation_id)
        uploaded += 1
    return {"uploaded": uploaded}


def pull_remote_head(store, master_key, transport):
    remote = transport.head()
    if not isinstance(remote, dict) or set(remote) != {"generationId"}:
        raise ValueError("remote continuity head is invalid")
    remote_head = remote["generationId"]
    if remote_head is not None and (
        not isinstance(remote_head, str) or not _GENERATION.fullmatch(remote_head)
    ):
        raise ValueError("remote continuity head is invalid")
    local = store.get_head()
    local_head = None if local is None else local["generation_id"]
    if remote_head is None or remote_head == local_head:
        return {"status": "unchanged", "generationId": local_head}

    chain = []
    seen = set()
    cursor = remote_head
    common = None
    while cursor is not None:
        if cursor in seen or len(seen) >= 500:
            raise ValueError("remote continuity chain is invalid")
        seen.add(cursor)
        try:
            store.get_generation(cursor)
            common = cursor
            break
        except ValueError:
            pass
        envelope = transport.download(cursor)
        plaintext = decrypt_generation(master_key, envelope)
        generation, artifacts = unpack_generation(plaintext)
        if (
            generation["generation_id"] != envelope["generation_id"]
            or generation["parent_generation_id"]
            != envelope["parent_generation_id"]
            or generation["generation_id"] != cursor
        ):
            raise ValueError("remote continuity metadata does not match bundle")
        chain.append((generation, artifacts))
        cursor = generation["parent_generation_id"]

    with store.lock("continuity-pull"):
        current = store.get_head()
        current_id = None if current is None else current["generation_id"]
        for generation, artifacts in reversed(chain):
            store.install_generation(generation, artifacts)
        if current_id != local_head or common != local_head:
            return {
                "status": "conflict",
                "localHead": current_id,
                "remoteHead": remote_head,
            }
        if not store.activate_imported_generation(remote_head, local_head):
            return {
                "status": "conflict",
                "localHead": current_id,
                "remoteHead": remote_head,
            }
        return {"status": "activated", "generationId": remote_head}


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise urllib.error.HTTPError(req.full_url, code, msg, headers, fp)


def complete_pairing(base_url, body, timeout=15, opener=None):
    base_url = validate_https_origin(base_url)
    if not isinstance(timeout, (int, float)) or not 1 <= timeout <= 60:
        raise ValueError("continuity timeout is invalid")
    if not isinstance(body, dict):
        raise ValueError("pairing request is invalid")
    payload = canonical_json(body).encode("utf-8")
    if len(payload) > 8192:
        raise ValueError("pairing request is too large")
    request = urllib.request.Request(
        base_url + "/v1/devices/pair/complete",
        data=payload,
        headers={"Accept": "application/json", "Content-Type": "application/json"},
        method="POST",
    )
    if opener is None:
        opener = urllib.request.build_opener(_NoRedirect())
    response = opener.open(request, timeout=timeout)
    with response:
        status = getattr(response, "status", None)
        content_type = response.headers.get_content_type()
        raw = response.read(8193)
    if status != 201 or content_type != "application/json" or len(raw) > 8192:
        raise ValueError("pairing response is invalid")
    try:
        value = json.loads(raw.decode("utf-8", errors="strict"))
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError("pairing response is invalid") from exc
    if (
        not isinstance(value, dict)
        or set(value) != {"deviceId", "deviceToken"}
        or not isinstance(value.get("deviceId"), str)
        or not _DEVICE.fullmatch(value["deviceId"])
        or not isinstance(value.get("deviceToken"), str)
        or not _TOKEN.fullmatch(value["deviceToken"])
    ):
        raise ValueError("pairing response is invalid")
    return value


class HttpsContinuityTransport:
    def __init__(self, base_url, device_token, timeout=15):
        base_url = validate_https_origin(base_url)
        if not isinstance(device_token, str) or not _TOKEN.fullmatch(device_token):
            raise ValueError("device token is invalid")
        if not isinstance(timeout, (int, float)) or not 1 <= timeout <= 60:
            raise ValueError("continuity timeout is invalid")
        self.base_url = base_url
        self.device_token = device_token
        self.timeout = timeout
        self.opener = urllib.request.build_opener(_NoRedirect())

    def _request(self, method, path, body=None):
        payload = None if body is None else canonical_json(body).encode("utf-8")
        headers = {
            "Authorization": "Bearer " + self.device_token,
            "Accept": "application/json",
        }
        if payload is not None:
            headers["Content-Type"] = "application/json"
        request = urllib.request.Request(
            self.base_url + path,
            data=payload,
            headers=headers,
            method=method,
        )
        try:
            response = self.opener.open(request, timeout=self.timeout)
        except urllib.error.HTTPError as exc:
            if exc.code != 409:
                raise
            response = exc
        with response:
            content_type = response.headers.get_content_type()
            raw = response.read(MAX_RESPONSE_BYTES + 1)
        if content_type != "application/json" or len(raw) > MAX_RESPONSE_BYTES:
            raise ValueError("continuity server response is invalid")
        try:
            return json.loads(raw.decode("utf-8", errors="strict"))
        except (UnicodeError, json.JSONDecodeError) as exc:
            raise ValueError("continuity server response is invalid") from exc

    def upload(self, envelope):
        return self._request("POST", "/v1/continuity/generations", envelope)

    def head(self):
        return self._request("GET", "/v1/continuity/head")

    def download(self, generation_id):
        if not isinstance(generation_id, str) or not _GENERATION.fullmatch(generation_id):
            raise ValueError("generation_id is invalid")
        return self._request("GET", "/v1/continuity/generations/" + generation_id)
