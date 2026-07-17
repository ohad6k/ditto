import base64
import datetime
import hashlib
import json
import os
import re
import stat
import tempfile

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric.x25519 import (
    X25519PrivateKey,
    X25519PublicKey,
)
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives.kdf.scrypt import Scrypt


ENVELOPE_SCHEMA = "emulo.continuity-envelope/v1"
DEVICE_WRAP_SCHEMA = "emulo.continuity-device-wrap/v1"
RECOVERY_WRAP_SCHEMA = "emulo.continuity-recovery-wrap/v1"
MAX_PLAINTEXT_BYTES = 192 * 1024

_GENERATION = re.compile(r"^gen_[a-f0-9]{20}$")
_DEVICE = re.compile(r"^dev_[a-f0-9]{32}$")
_UTC_SECONDS = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")
_B64URL = re.compile(r"^[A-Za-z0-9_-]+$")


def _canonical(value):
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def _b64(value):
    return base64.urlsafe_b64encode(value).decode("ascii").rstrip("=")


def _unb64(value, label, expected=None, maximum=None):
    if not isinstance(value, str) or not value or not _B64URL.fullmatch(value):
        raise ValueError(label + " is invalid")
    try:
        padding = "=" * ((4 - len(value) % 4) % 4)
        decoded = base64.b64decode(
            value + padding,
            altchars=b"-_",
            validate=True,
        )
    except (ValueError, TypeError) as exc:
        raise ValueError(label + " is invalid") from exc
    if expected is not None and len(decoded) != expected:
        raise ValueError(label + " is invalid")
    if maximum is not None and len(decoded) > maximum:
        raise ValueError(label + " is too large")
    return decoded


def _key(value, label="master key"):
    if not isinstance(value, bytes) or len(value) != 32:
        raise ValueError(label + " is invalid")
    return value


def _timestamp(value):
    if not isinstance(value, str) or not _UTC_SECONDS.fullmatch(value):
        raise ValueError("created_at is invalid")
    try:
        datetime.datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ")
    except ValueError as exc:
        raise ValueError("created_at is invalid") from exc
    return value


def generate_master_key(random_bytes=os.urandom):
    value = random_bytes(32)
    return _key(value)


def generate_recovery_secret(random_bytes=os.urandom):
    value = random_bytes(32)
    if not isinstance(value, bytes) or len(value) != 32:
        raise ValueError("random source returned invalid recovery bytes")
    return _b64(value)


def _envelope_metadata(
    generation_id,
    parent_generation_id,
    author_device_id,
    created_at,
):
    if not isinstance(generation_id, str) or not _GENERATION.fullmatch(generation_id):
        raise ValueError("generation_id is invalid")
    if parent_generation_id is not None and (
        not isinstance(parent_generation_id, str)
        or not _GENERATION.fullmatch(parent_generation_id)
    ):
        raise ValueError("parent_generation_id is invalid")
    if not isinstance(author_device_id, str) or not _DEVICE.fullmatch(author_device_id):
        raise ValueError("author_device_id is invalid")
    return {
        "schema_version": ENVELOPE_SCHEMA,
        "generation_id": generation_id,
        "parent_generation_id": parent_generation_id,
        "author_device_id": author_device_id,
        "created_at": _timestamp(created_at),
    }


def encrypt_generation(
    master_key,
    *,
    generation_id,
    parent_generation_id,
    author_device_id,
    created_at,
    plaintext,
    random_bytes=os.urandom,
):
    master_key = _key(master_key)
    if not isinstance(plaintext, bytes):
        raise ValueError("plaintext must be bytes")
    if len(plaintext) > MAX_PLAINTEXT_BYTES:
        raise ValueError("plaintext is too large")
    metadata = _envelope_metadata(
        generation_id,
        parent_generation_id,
        author_device_id,
        created_at,
    )
    nonce = random_bytes(12)
    if not isinstance(nonce, bytes) or len(nonce) != 12:
        raise ValueError("random source returned invalid nonce")
    ciphertext = AESGCM(master_key).encrypt(nonce, plaintext, _canonical(metadata))
    return {
        **metadata,
        "nonce": _b64(nonce),
        "ciphertext": _b64(ciphertext),
        "ciphertext_sha256": hashlib.sha256(ciphertext).hexdigest(),
    }


def decrypt_generation(master_key, envelope):
    master_key = _key(master_key)
    if not isinstance(envelope, dict) or set(envelope) != {
        "schema_version",
        "generation_id",
        "parent_generation_id",
        "author_device_id",
        "created_at",
        "nonce",
        "ciphertext",
        "ciphertext_sha256",
    }:
        raise ValueError("encrypted envelope is invalid")
    metadata = _envelope_metadata(
        envelope["generation_id"],
        envelope["parent_generation_id"],
        envelope["author_device_id"],
        envelope["created_at"],
    )
    nonce = _unb64(envelope["nonce"], "nonce", expected=12)
    ciphertext = _unb64(
        envelope["ciphertext"],
        "ciphertext",
        maximum=MAX_PLAINTEXT_BYTES + 16,
    )
    digest = envelope["ciphertext_sha256"]
    if (
        not isinstance(digest, str)
        or not re.fullmatch(r"[a-f0-9]{64}", digest)
        or hashlib.sha256(ciphertext).hexdigest() != digest
    ):
        raise ValueError("ciphertext digest is invalid")
    return AESGCM(master_key).decrypt(nonce, ciphertext, _canonical(metadata))


def generate_device_key_pair():
    private = X25519PrivateKey.generate()
    private_bytes = private.private_bytes(
        serialization.Encoding.Raw,
        serialization.PrivateFormat.Raw,
        serialization.NoEncryption(),
    )
    public_bytes = private.public_key().public_bytes(
        serialization.Encoding.Raw,
        serialization.PublicFormat.Raw,
    )
    return private_bytes, public_bytes


def device_public_key(device_private_key):
    if not isinstance(device_private_key, bytes) or len(device_private_key) != 32:
        raise ValueError("device private key is invalid")
    return X25519PrivateKey.from_private_bytes(device_private_key).public_key().public_bytes(
        serialization.Encoding.Raw,
        serialization.PublicFormat.Raw,
    )


def _device_wrap_aad(device_public_key, ephemeral_public_key, salt):
    return _canonical(
        {
            "schema_version": DEVICE_WRAP_SCHEMA,
            "device_public_key": _b64(device_public_key),
            "ephemeral_public_key": _b64(ephemeral_public_key),
            "salt": _b64(salt),
        }
    )


def _device_kek(private_key, peer_public_key, salt):
    shared = private_key.exchange(peer_public_key)
    return HKDF(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        info=b"emulo-continuity-device-wrap-v1",
    ).derive(shared)


def wrap_master_key_for_device(master_key, device_public_key, random_bytes=os.urandom):
    master_key = _key(master_key)
    if not isinstance(device_public_key, bytes) or len(device_public_key) != 32:
        raise ValueError("device public key is invalid")
    recipient = X25519PublicKey.from_public_bytes(device_public_key)
    ephemeral = X25519PrivateKey.generate()
    ephemeral_public = ephemeral.public_key().public_bytes(
        serialization.Encoding.Raw,
        serialization.PublicFormat.Raw,
    )
    salt = random_bytes(16)
    nonce = random_bytes(12)
    if not isinstance(salt, bytes) or len(salt) != 16:
        raise ValueError("random source returned invalid salt")
    if not isinstance(nonce, bytes) or len(nonce) != 12:
        raise ValueError("random source returned invalid nonce")
    aad = _device_wrap_aad(device_public_key, ephemeral_public, salt)
    ciphertext = AESGCM(_device_kek(ephemeral, recipient, salt)).encrypt(
        nonce, master_key, aad
    )
    return {
        "schema_version": DEVICE_WRAP_SCHEMA,
        "device_public_key": _b64(device_public_key),
        "ephemeral_public_key": _b64(ephemeral_public),
        "salt": _b64(salt),
        "nonce": _b64(nonce),
        "ciphertext": _b64(ciphertext),
    }


def unwrap_master_key_for_device(wrapped, device_private_key):
    if not isinstance(wrapped, dict) or set(wrapped) != {
        "schema_version",
        "device_public_key",
        "ephemeral_public_key",
        "salt",
        "nonce",
        "ciphertext",
    } or wrapped.get("schema_version") != DEVICE_WRAP_SCHEMA:
        raise ValueError("device wrapped key is invalid")
    if not isinstance(device_private_key, bytes) or len(device_private_key) != 32:
        raise ValueError("device private key is invalid")
    private = X25519PrivateKey.from_private_bytes(device_private_key)
    expected_public = private.public_key().public_bytes(
        serialization.Encoding.Raw,
        serialization.PublicFormat.Raw,
    )
    recipient_public = _unb64(
        wrapped["device_public_key"], "device public key", expected=32
    )
    if expected_public != recipient_public:
        raise ValueError("device wrapped key belongs to another device")
    ephemeral_public = _unb64(
        wrapped["ephemeral_public_key"], "ephemeral public key", expected=32
    )
    salt = _unb64(wrapped["salt"], "salt", expected=16)
    nonce = _unb64(wrapped["nonce"], "nonce", expected=12)
    ciphertext = _unb64(wrapped["ciphertext"], "ciphertext", expected=48)
    aad = _device_wrap_aad(recipient_public, ephemeral_public, salt)
    master_key = AESGCM(
        _device_kek(private, X25519PublicKey.from_public_bytes(ephemeral_public), salt)
    ).decrypt(nonce, ciphertext, aad)
    return _key(master_key)


def _recovery_aad(salt):
    return _canonical(
        {
            "schema_version": RECOVERY_WRAP_SCHEMA,
            "kdf": {"name": "scrypt", "n": 16384, "r": 8, "p": 1},
            "salt": _b64(salt),
        }
    )


def _recovery_kek(secret, salt):
    secret_bytes = _unb64(secret, "recovery secret", expected=32)
    return Scrypt(salt=salt, length=32, n=2**14, r=8, p=1).derive(secret_bytes)


def wrap_master_key_for_recovery(master_key, recovery_secret, random_bytes=os.urandom):
    master_key = _key(master_key)
    salt = random_bytes(16)
    nonce = random_bytes(12)
    if not isinstance(salt, bytes) or len(salt) != 16:
        raise ValueError("random source returned invalid salt")
    if not isinstance(nonce, bytes) or len(nonce) != 12:
        raise ValueError("random source returned invalid nonce")
    ciphertext = AESGCM(_recovery_kek(recovery_secret, salt)).encrypt(
        nonce, master_key, _recovery_aad(salt)
    )
    return {
        "schema_version": RECOVERY_WRAP_SCHEMA,
        "kdf": {"name": "scrypt", "n": 16384, "r": 8, "p": 1},
        "salt": _b64(salt),
        "nonce": _b64(nonce),
        "ciphertext": _b64(ciphertext),
    }


def unwrap_master_key_from_recovery(wrapped, recovery_secret):
    if not isinstance(wrapped, dict) or set(wrapped) != {
        "schema_version",
        "kdf",
        "salt",
        "nonce",
        "ciphertext",
    }:
        raise ValueError("recovery wrapped key is invalid")
    if wrapped.get("schema_version") != RECOVERY_WRAP_SCHEMA or wrapped.get("kdf") != {
        "name": "scrypt",
        "n": 16384,
        "r": 8,
        "p": 1,
    }:
        raise ValueError("recovery wrapped key is invalid")
    salt = _unb64(wrapped["salt"], "salt", expected=16)
    nonce = _unb64(wrapped["nonce"], "nonce", expected=12)
    ciphertext = _unb64(wrapped["ciphertext"], "ciphertext", expected=48)
    master_key = AESGCM(_recovery_kek(recovery_secret, salt)).decrypt(
        nonce, ciphertext, _recovery_aad(salt)
    )
    return _key(master_key)


def write_private_material(path, device_private_key, master_key):
    path = os.path.abspath(os.fspath(path))
    device_private_key = _key(device_private_key, "device private key")
    master_key = _key(master_key)
    parent = os.path.dirname(path)
    if not os.path.isdir(parent) or os.path.islink(parent):
        raise ValueError("private material path is invalid")
    if os.path.lexists(path) and (os.path.islink(path) or not os.path.isfile(path)):
        raise ValueError("private material path is invalid")
    payload = _canonical(
        {
            "schema_version": "emulo.continuity-private-material/v1",
            "device_private_key": _b64(device_private_key),
            "master_key": _b64(master_key),
        }
    ) + b"\n"
    descriptor, temporary = tempfile.mkstemp(
        prefix=".continuity-keys-",
        suffix=".tmp",
        dir=parent,
    )
    try:
        os.chmod(temporary, 0o600)
        with os.fdopen(descriptor, "wb") as handle:
            descriptor = None
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
        os.chmod(path, 0o600)
    finally:
        if descriptor is not None:
            os.close(descriptor)
        if os.path.exists(temporary):
            os.unlink(temporary)


def read_private_material(path):
    path = os.path.abspath(os.fspath(path))
    if os.path.islink(path) or not os.path.isfile(path):
        raise ValueError("private material path is invalid")
    if os.name != "nt" and stat.S_IMODE(os.stat(path).st_mode) & 0o077:
        raise ValueError("private material permissions are too broad")
    try:
        with open(path, "r", encoding="utf-8", errors="strict") as handle:
            value = json.load(handle)
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError("private material is invalid") from exc
    if not isinstance(value, dict) or set(value) != {
        "schema_version",
        "device_private_key",
        "master_key",
    } or value.get("schema_version") != "emulo.continuity-private-material/v1":
        raise ValueError("private material is invalid")
    return (
        _unb64(value["device_private_key"], "device private key", expected=32),
        _unb64(value["master_key"], "master key", expected=32),
    )
