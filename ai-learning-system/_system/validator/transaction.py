"""P08 — Transaction engine: manifest + OCC + recovery (spec mục 10.3, 10.3a/b).

Cam kết đúng (spec vá v2.3): os.replace CHỈ atomic 1-file/1-filesystem. KHÔNG hứa atomic
cả transaction. Toàn vẹn giữ bằng: manifest bền vững (atomic_write_manifest) + RECOVER-FIRST
roll-forward. Không partial commit âm thầm; không ghi đè sửa tay (OCC hai mốc).

Ranh giới: module là CƠ CHẾ ghi. REGEN view là điểm nối P09/P10 (caller đưa writes đã đủ view).
"""
from __future__ import annotations

import json
import os
import shutil
import tempfile
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path

import vault_io as VIO

# vùng transient (validator bỏ qua như INV-20); .tx phải CÙNG GỐC với đích (tránh cross-device)
TX_DIRNAME = ".tx"
_IGNORE_IN_OVERLAY = {".tx", "_scratch", ".cache", ".git", "__pycache__", ".pytest_cache", ".venv"}
_RETRY_DELAYS = (0.1, 0.2, 0.5, 1.0, 2.0)  # spec 10.3: backoff chống cloud-lock (WinError 32)

# indirection để test fault-injection monkeypatch được (không sleep thật, ép PermissionError)
_os_replace = os.replace
_os_remove = os.remove
_sleep = time.sleep


class TxError(Exception):
    """Lỗi transaction mang mã spec 10.4."""
    def __init__(self, code: str, message: str):
        super().__init__(f"[{code}] {message}")
        self.code = code
        self.message = message


# ---- atomic manifest ----------------------------------------------------
def atomic_write_manifest(manifest_path: Path, data: dict) -> None:
    """Ghi manifest bền vững: tmp → flush+fsync → os.replace → fsync dir (spec 10.3).
    Crash giữa chừng ⇒ hoặc bản cũ hoặc bản mới, KHÔNG JSON rách."""
    manifest_path = Path(manifest_path)
    tmp = manifest_path.with_suffix(".tmp")
    blob = json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True).encode("utf-8")
    with open(tmp, "wb") as f:
        f.write(blob)
        f.flush()
        os.fsync(f.fileno())
    _os_replace(tmp, manifest_path)
    _fsync_dir(manifest_path.parent)


def _fsync_dir(path: Path) -> None:
    """fsync thư mục nếu OS hỗ trợ (Windows không hỗ trợ fd thư mục → bỏ qua an toàn)."""
    try:
        fd = os.open(str(path), os.O_RDONLY)
        try:
            os.fsync(fd)
        finally:
            os.close(fd)
    except (OSError, AttributeError, PermissionError):
        pass


def _prune_empty_dirs(deleted_file: Path, root: Path) -> None:
    """Sau khi xoá 1 file, dọn các thư mục cha RỖNG đi lên (dừng ở root / thư mục không rỗng).
    Chỉ rmdir thư mục rỗng ⇒ không mất dữ liệu; idempotent ⇒ an toàn cho recovery/crash.
    Cần cho /forget: xoá file lesson để lại dir rỗng sẽ bị validator bắt E-INDEX-MISMATCH."""
    root = Path(root)
    d = Path(deleted_file).parent
    while d != root and d != d.parent and d.is_dir() and not any(d.iterdir()):
        try:
            d.rmdir()
        except OSError:
            break
        d = d.parent


def _read_text_safe(path: Path) -> str:
    """Đọc text UTF-8; trả '' nếu lỗi (dùng cho baseline/after INV-11, không được ném)."""
    try:
        return Path(path).read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return ""


def _write_bytes_durable(path: Path, data: bytes) -> None:
    """Ghi bytes BỀN VỮNG: write → flush → os.fsync (spec 10.3 — cùng kỷ luật với manifest).
    Dùng cho staged files để dữ liệu commit không thua độ bền của manifest (tránh lỗ hổng
    'rename mà chưa fsync data': crash sau os.replace có thể mất data nếu block chưa chạm đĩa)."""
    with open(path, "wb") as f:
        f.write(data)
        f.flush()
        os.fsync(f.fileno())


def _read_manifest(manifest_path: Path) -> dict | None:
    """Đọc manifest; nếu bản chính rách nhưng còn .tmp nguyên vẹn thì dùng .tmp (spec 10.3)."""
    for p in (manifest_path, manifest_path.with_suffix(".tmp")):
        if p.is_file():
            try:
                return json.loads(p.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, UnicodeDecodeError):
                continue
    return None


# ---- retry rename/remove (cloud-lock) ----------------------------------
def _replace_with_retry(src: Path, dst: Path) -> None:
    _run_with_retry(lambda: _os_replace(src, dst), what=f"replace {dst}")


def _remove_with_retry(target: Path) -> None:
    def _op():
        if Path(target).exists():
            _os_remove(target)
    _run_with_retry(_op, what=f"remove {target}")


def _run_with_retry(op, what: str) -> None:
    last = None
    for i in range(len(_RETRY_DELAYS) + 1):
        try:
            op()
            return
        except (PermissionError, OSError) as e:
            last = e
            if i < len(_RETRY_DELAYS):
                _sleep(_RETRY_DELAYS[i])
    raise TxError("E-TX-PARTIAL", f"hết lượt retry khi {what}: {last!r}")


# ---- data model ---------------------------------------------------------
@dataclass
class Write:
    """Một thao tác ghi/xoá trên file đích (relpath so với root)."""
    target: str
    content: bytes | None = None          # None khi op='delete'
    expected_read_hash: str | None = None  # None = file mới (spec 10.3 bước 0b)
    op: str = "write"                      # 'write' | 'delete'


@dataclass
class Tombstone:
    """Xoá có thẩm quyền (spec 10.3a) — bền vững trong manifest trước khi replace."""
    op: str
    scope: str
    lesson_id: str
    item_ids: list[str] = field(default_factory=list)
    reason: str = ""
    at: str = ""
    confirmed_by_user: bool = False

    def to_dict(self) -> dict:
        return {"op": self.op, "scope": self.scope, "lesson_id": self.lesson_id,
                "item_ids": list(self.item_ids), "reason": self.reason, "at": self.at,
                "confirmed_by_user": self.confirmed_by_user}


# ---- Transaction (một gốc) ---------------------------------------------
class Transaction:
    def __init__(self, root: Path, level: str = "full", tx_id: str | None = None,
                 sibling_roots: list[str] | None = None, now=None):
        self.root = Path(root)
        self.level = level
        self.now = now  # mốc 'today' cho INV-05 khi validate_staged (spec §5.4); None → now UTC thật
        self.tx_id = tx_id or f"{int(time.time() * 1000)}-{uuid.uuid4().hex[:8]}"
        self.sibling_roots = sibling_roots or []
        self.tx_dir = self.root / TX_DIRNAME / self.tx_id
        self.manifest_path = self.tx_dir / "manifest.json"
        self._writes: list[Write] = []
        self.manifest: dict = {}

    # ----- paths -----
    def _staged_path(self, target: str) -> Path:
        return self.tx_dir / "staged" / target

    def _backup_path(self, target: str) -> Path:
        return self.tx_dir / "backup" / target

    def _save(self) -> None:
        atomic_write_manifest(self.manifest_path, self.manifest)

    # ----- BEGIN -----
    def begin(self, writes: list[Write], tombstones: list[Tombstone] | None = None) -> None:
        """Bọc _begin_impl: nếu lỗi TRƯỚC khi manifest bền vững (vd E-STALE-CONTEXT), dọn .tx/<id> dở
        (chưa có transaction thật để truy vết; tránh orphan backup rò rỉ). tx_id unique nên rmtree an toàn."""
        try:
            self._begin_impl(writes, tombstones)
        except BaseException:
            shutil.rmtree(self.tx_dir, ignore_errors=True)
            raise

    def _begin_impl(self, writes: list[Write], tombstones: list[Tombstone] | None = None) -> None:
        self._writes = list(writes)
        (self.tx_dir / "staged").mkdir(parents=True, exist_ok=True)
        (self.tx_dir / "backup").mkdir(parents=True, exist_ok=True)
        files = []
        for w in writes:
            target_abs = self.root / w.target
            current = VIO.content_hash(target_abs)
            # OCC mốc 1: T-read → BEGIN
            if w.expected_read_hash is not None and current != w.expected_read_hash:
                raise TxError("E-STALE-CONTEXT",
                              f"{w.target}: file đổi sau khi đọc context "
                              f"(đọc {w.expected_read_hash}, hiện {current})")
            backup_hash = None
            if current is not None:
                bpath = self._backup_path(w.target)
                bpath.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(target_abs, bpath)
                backup_hash = current
            files.append({
                "target": w.target, "op": w.op,
                "expected_read_hash": w.expected_read_hash,
                "before_hash": current, "backup_hash": backup_hash,
                "staged_hash": None, "committed": False,
            })
        self.manifest = {
            "tx_id": self.tx_id, "root": self.root.name, "level": self.level,
            "state": "prepared", "created_at": _now_iso(),
            "sibling_roots": self.sibling_roots,
            "files": files,
            "tombstones": [t.to_dict() for t in (tombstones or [])],
        }
        self._save()

    # ----- STAGE -----
    def stage(self) -> None:
        by_target = {w.target: w for w in self._writes}
        for f in self.manifest["files"]:
            w = by_target[f["target"]]
            if w.op == "delete":
                f["staged_hash"] = None  # marker xoá
                continue
            sp = self._staged_path(f["target"])
            sp.parent.mkdir(parents=True, exist_ok=True)
            data = w.content if w.content is not None else b""
            _write_bytes_durable(sp, data)  # staged bền vững trước khi commit repoint
            f["staged_hash"] = "sha256:" + _sha_bytes(data)
        self._save()

    # ----- VALIDATE (overlay) -----
    def validate_staged(self, system_root: Path, level: str | None = None):
        """Chạy validator trên OVERLAY = vault thật + staged applied (spec 10.3 bước 4).
        FULL = TOÀN BỘ INV-01..26 (core + semantic, spec 10.8) → dùng validate_full_semantic,
        KHÔNG chỉ core (nếu không /review /done sẽ bỏ lọt INV-07/12../26 tại điểm đóng sổ).
        Trả Report của validate.py."""
        import validate as V  # lazy: tránh phụ thuộc vòng lúc import
        level = level or self.level
        overlay = self._build_overlay()
        try:
            rep = V.Report()
            if level == "light":
                V.validate_light(overlay, None, rep)
            else:
                # real_vault_root=self.root (DEC-073): overlay là thư mục TEMP, KHÔNG có sibling exam/;
                # _check_exam_results phải resolve ref bài nộp về vault THẬT (self.root) mới thấy exam/.
                V.validate_full_semantic(Path(system_root), overlay, rep, now=self.now, real_vault_root=self.root)
                self._check_review_preservation(rep)   # INV-11 (diff backup↔staged)
                self._check_status_transitions(rep)    # INV-06 (diff backup↔staged)
            return rep
        finally:
            shutil.rmtree(overlay, ignore_errors=True)

    def _check_review_preservation(self, rep) -> None:
        """INV-11 (spec 10.3a): so review-state backup(baseline) ↔ staged(after) cho mỗi lesson_state.md.
        Item in_review/need_redo biến mất phải có tombstone khớp item_id, nếu không → E-REVIEW-LOST.
        Đây là kiểm DIFF nên PHẢI ở tầng transaction (có backup+staged+tombstone), KHÔNG ở validate_full_*."""
        import validate as V
        tomb_ids = set()
        for t in self.manifest.get("tombstones", []):
            tomb_ids.update(t.get("item_ids", []))
        for f in self.manifest["files"]:
            target = f["target"]
            if not target.endswith("lesson_state.md"):
                continue
            bpath = self._backup_path(target)
            baseline = V.extract_review_states(_read_text_safe(bpath)) if bpath.is_file() else {}
            if f["op"] == "delete":
                after = {}
            else:
                spath = self._staged_path(target)
                after = V.extract_review_states(_read_text_safe(spath)) if spath.is_file() else {}
            V.check_review_not_lost(baseline, after, tomb_ids, rep, target)

    def _check_status_transitions(self, rep) -> None:
        """INV-06 (spec 6.1): so status lesson backup(before) ↔ staged(after) cho mỗi lesson_state.md.
        Cạnh chuyển không hợp lệ → E-STATE-ILLEGAL. Chỉ kiểm khi CÓ backup (không phải file mới/xoá)."""
        import validate as V
        for f in self.manifest["files"]:
            target = f["target"]
            if not target.endswith("lesson_state.md") or f["op"] == "delete":
                continue
            bpath = self._backup_path(target)
            if not bpath.is_file():
                continue  # file mới → không phải chuyển trạng thái
            before = V.extract_lesson_status(_read_text_safe(bpath))
            spath = self._staged_path(target)
            after = V.extract_lesson_status(_read_text_safe(spath)) if spath.is_file() else None
            V.check_status_transition(before, after, rep, target)

    def _build_overlay(self) -> Path:
        tmp = Path(tempfile.mkdtemp(prefix=f"tx_overlay_{self.tx_id}_"))
        for src in self.root.rglob("*"):
            rel = src.relative_to(self.root)
            if _IGNORE_IN_OVERLAY & set(rel.parts):
                continue
            dst = tmp / rel
            if src.is_dir():
                dst.mkdir(parents=True, exist_ok=True)
            else:
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, dst)
        for f in self.manifest["files"]:
            dst = tmp / f["target"]
            if f["op"] == "delete":
                if dst.exists():
                    dst.unlink()
                _prune_empty_dirs(dst, tmp)  # dir rỗng sau xoá không được lọt vào overlay
            else:
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(self._staged_path(f["target"]), dst)
        return tmp

    # ----- OCC RE-CHECK (mốc 2: BEGIN → COMMIT) -----
    def occ_recheck(self) -> None:
        for f in self.manifest["files"]:
            current = VIO.content_hash(self.root / f["target"])
            if current != f["before_hash"]:
                self.abort()  # spec 10.3: lệch OCC mốc-2 → ABORT (mark terminal; không để 'prepared' treo → .tx rò rỉ)
                raise TxError("E-CONCURRENT-EDIT",
                              f"{f['target']}: file đích bị sửa trong lúc tx chạy "
                              f"(baseline {f['before_hash']}, hiện {current})")

    # ----- COMMIT (roll-forward, không rollback sau 'committing') -----
    def commit(self) -> None:
        self.manifest["state"] = "committing"
        self._save()
        try:
            for f in sorted(self.manifest["files"], key=lambda x: x["target"]):
                self._apply_commit(f)
                f["committed"] = True
                self._save()
        except TxError:
            self.manifest["state"] = "interrupted"
            self._save()
            raise
        self.manifest["state"] = "committed"
        self._save()
        _materialize_log(self.root, self.manifest)
        self._cleanup()

    def _apply_commit(self, f: dict) -> None:
        target_abs = self.root / f["target"]
        if f["op"] == "delete":
            _remove_with_retry(target_abs)
            _prune_empty_dirs(target_abs, self.root)  # dọn dir rỗng sau xoá (spec /forget)
        else:
            target_abs.parent.mkdir(parents=True, exist_ok=True)
            _replace_with_retry(self._staged_path(f["target"]), target_abs)
            _fsync_dir(target_abs.parent)  # bền vững rename (best-effort; Windows no-op an toàn)

    def abort(self) -> None:
        """FAIL trước 'committing' → file thật chưa đụng; giữ .tx để truy vết (spec 6b)."""
        self.manifest["state"] = "aborted"
        self._save()

    def _cleanup(self) -> None:
        shutil.rmtree(self.tx_dir, ignore_errors=True)


# ---- helpers ------------------------------------------------------------
def _sha_bytes(b: bytes) -> str:
    import hashlib
    return hashlib.sha256(b).hexdigest()


def _now_iso() -> str:
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _materialize_log(root: Path, manifest: dict) -> None:
    """transaction_log.md = VIEW dẫn xuất từ manifest (spec 10.3a). Idempotent theo tx_id."""
    log_path = root / "transaction_log.md"
    lines = [f"## tx {manifest['tx_id']} — {manifest['state']} @ {manifest.get('created_at', '')}"]
    for f in manifest["files"]:
        lines.append(f"- {f['op']}: {f['target']} (staged={f['staged_hash']})")
    for t in manifest.get("tombstones", []):
        lines.append(f"- tombstone: {t['scope']} {t['lesson_id']} items={t['item_ids']} "
                     f"reason={t['reason']!r} confirmed={t['confirmed_by_user']}")
    entry = "\n".join(lines) + "\n\n"
    existing = log_path.read_text(encoding="utf-8") if log_path.is_file() else ""
    if f"## tx {manifest['tx_id']} " in existing:  # đã materialize (idempotent)
        return
    log_path.write_text(existing + entry, encoding="utf-8")


# ---- RECOVERY -----------------------------------------------------------
def _tx_root_dir(root: Path) -> Path:
    return Path(root) / TX_DIRNAME


def scan_incomplete(root: Path) -> list[Path]:
    """Trả danh sách manifest có state committing/interrupted (RECOVER-FIRST)."""
    out = []
    txroot = _tx_root_dir(root)
    if not txroot.is_dir():
        return out
    for d in sorted(txroot.iterdir()):
        m = _read_manifest(d / "manifest.json")
        # 'committed' + còn .tx = crash giữa (state=committed đã lưu) và (materialize_log/cleanup) → finalize
        if m and m.get("state") in ("committing", "interrupted", "committed"):
            out.append(d / "manifest.json")
    return out


def recover(root: Path, all_roots: dict[str, Path] | None = None) -> list[str]:
    """RECOVER-FIRST: hoàn tất roll-forward hoặc chặn E-TX-PARTIAL (spec 10.3).
    all_roots: map tên-gốc→Path để kiểm multi-root cùng tx_id. Trả list tx_id đã xử lý."""
    handled = []
    for manifest_path in scan_incomplete(root):
        m = _read_manifest(manifest_path)
        if m is None:
            raise TxError("E-TX-PARTIAL", f"manifest hỏng: {manifest_path}")
        _check_multiroot(m, all_roots)
        _recover_one(root, manifest_path, m)
        handled.append(m["tx_id"])
    return handled


def _check_multiroot(m: dict, all_roots: dict[str, Path] | None) -> None:
    siblings = m.get("sibling_roots") or []
    if not siblings:
        return
    if all_roots is None:
        raise TxError("E-TX-PARTIAL",
                      f"tx {m['tx_id']} multi-root nhưng không cấp all_roots để kiểm")
    for rname in siblings:
        rpath = all_roots.get(rname)
        if rpath is None or not (Path(rpath) / TX_DIRNAME / m["tx_id"] / "manifest.json").is_file():
            raise TxError("E-TX-PARTIAL",
                          f"tx {m['tx_id']} thiếu manifest ở root {rname!r} — không recovery an toàn")


def _recover_one(root: Path, manifest_path: Path, m: dict) -> None:
    root = Path(root)
    pending = []
    for f in m["files"]:
        target_abs = root / f["target"]
        cur = VIO.content_hash(target_abs)
        if f["op"] == "delete":
            if cur is None:
                f["committed"] = True                      # đã xoá
            elif cur == f["before_hash"]:
                pending.append(f)                          # chưa xoá
            else:
                raise TxError("E-TX-PARTIAL",
                              f"{f['target']}: hash lạ khi recover delete (hiện {cur})")
        else:
            if cur == f["staged_hash"]:
                f["committed"] = True                      # đã commit
            elif cur in (f["before_hash"], f["backup_hash"]):
                pending.append(f)                          # chưa commit
            else:
                raise TxError("E-TX-PARTIAL",
                              f"{f['target']}: hash lạ khi recover (hiện {cur}) — cần xử lý tay")
    tx_dir = manifest_path.parent
    for f in pending:
        if f["op"] == "delete":
            _remove_with_retry(root / f["target"])
            _prune_empty_dirs(root / f["target"], root)  # nhất quán với commit
        else:
            (root / f["target"]).parent.mkdir(parents=True, exist_ok=True)
            _replace_with_retry(tx_dir / "staged" / f["target"], root / f["target"])
        f["committed"] = True
    m["state"] = "committed"
    atomic_write_manifest(manifest_path, m)
    _materialize_log(root, m)                              # roll-forward tombstone/log từ manifest
    shutil.rmtree(tx_dir, ignore_errors=True)
