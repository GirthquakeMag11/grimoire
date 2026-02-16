"""
A clean dataclass for path and file information with consistent snapshot semantics.
"""
from __future__ import annotations

import dataclasses
from dataclasses import dataclass
from pathlib import Path
from datetime import datetime, timezone
import os
import stat
import mimetypes

# Platform-specific imports
try:
    import pwd
    import grp
    HAS_UNIX_USERS = True
except ImportError:
    HAS_UNIX_USERS = False


@dataclass(frozen=True, slots=True)
class FileMetadata:
    """File size and timestamps."""
    size_bytes: int
    modified: datetime
    accessed: datetime
    status_changed: datetime


@dataclass(frozen=True, slots=True)
class Permissions:
    """File permissions and ownership."""
    mode: int
    octal: str
    readable: bool
    writable: bool
    executable: bool
    owner: str | None
    group: str | None
    owner_id: int
    group_id: int


@dataclass(frozen=True, slots=True)
class FileType:
    """Detailed file type information."""
    is_file: bool
    is_dir: bool
    is_symlink: bool
    is_mount: bool
    is_socket: bool
    is_fifo: bool
    is_block_device: bool
    is_char_device: bool
    mime_type: str | None = None
    mime_encoding: str | None = None


def get_stat(path: Path) -> tuple[os.stat_result | None, os.stat_result | None]:
    """Get stat and lstat, returning (stat_result, lstat_result) or (None, None)."""
    try:
        return path.stat(), path.lstat()
    except (OSError, PermissionError):
        return None, None


def create_metadata(st: os.stat_result) -> FileMetadata:
    """Create FileMetadata from stat result."""
    return FileMetadata(
        size_bytes=st.st_size,
        modified=datetime.fromtimestamp(st.st_mtime, tz=timezone.utc),
        accessed=datetime.fromtimestamp(st.st_atime, tz=timezone.utc),
        status_changed=datetime.fromtimestamp(st.st_ctime, tz=timezone.utc)
    )


def get_username(uid: int) -> str | None:
    """Get username from UID, returns None on Windows."""
    if not HAS_UNIX_USERS:
        return None
    try:
        return pwd.getpwuid(uid).pw_name  # type: ignore[attr-defined]
    except (KeyError, OSError):
        return str(uid)


def get_groupname(gid: int) -> str | None:
    """Get group name from GID, returns None on Windows."""
    if not HAS_UNIX_USERS:
        return None
    try:
        return grp.getgrgid(gid).gr_name  # type: ignore[attr-defined]
    except (KeyError, OSError):
        return str(gid)


def create_permissions(st: os.stat_result, path: Path) -> Permissions:
    """Create Permissions from stat result and path."""
    return Permissions(
        mode=st.st_mode,
        octal=oct(stat.S_IMODE(st.st_mode)),
        readable=os.access(path, os.R_OK),
        writable=os.access(path, os.W_OK),
        executable=os.access(path, os.X_OK),
        owner=get_username(st.st_uid),
        group=get_groupname(st.st_gid),
        owner_id=st.st_uid,
        group_id=st.st_gid
    )


def create_file_type(path: Path, lst: os.stat_result) -> FileType:
    """Create FileType from path and lstat result."""
    is_file = path.is_file()
    mime_type, mime_encoding = mimetypes.guess_type(str(path)) if is_file else (None, None)

    return FileType(
        is_file=is_file,
        is_dir=path.is_dir(),
        is_symlink=path.is_symlink(),
        is_mount=path.is_mount(),
        is_socket=stat.S_ISSOCK(lst.st_mode),
        is_fifo=stat.S_ISFIFO(lst.st_mode),
        is_block_device=stat.S_ISBLK(lst.st_mode),
        is_char_device=stat.S_ISCHR(lst.st_mode),
        mime_type=mime_type,
        mime_encoding=mime_encoding
    )


def get_child_count(path: Path, is_dir: bool) -> int | None:
    """Count children in directory, returns None if not a dir or can't read."""
    if not is_dir:
        return None
    try:
        return sum(1 for _ in path.iterdir())
    except (PermissionError, OSError):
        return None


def get_symlink_target(path: Path, is_symlink: bool) -> str | None:
    """Get symlink target, returns None if not a symlink or can't read."""
    if not is_symlink:
        return None
    try:
        return str(path.readlink())
    except (OSError, NotImplementedError):
        return None


@dataclass
class PathInfo:
    """
    Extract comprehensive information about a file or directory path.

    This creates a consistent snapshot of the file state at initialization time.
    If the file changes after creation, create a new PathInfo instance or call refresh().
    """

    input_path: dataclasses.InitVar[str | Path]
    path: Path = dataclasses.field(init=False)
    exists: bool = False
    metadata: FileMetadata | None = None
    permissions: Permissions | None = None
    file_type: FileType | None = None
    symlink_target: str | None = None
    child_count: int | None = None
    inode: int | None = None
    device: int | None = None
    hard_link_count: int | None = None

    def __post_init__(self, input_path: str | Path):
        self.path = Path(input_path).resolve()
        self.refresh()

    def refresh(self):
        """Reload all file system information to get current state."""
        self.exists = self.path.exists()

        if not self.exists:
            return

        st, lst = get_stat(self.path)

        if st is None or lst is None:
            return

        self.metadata = create_metadata(st)
        self.permissions = create_permissions(st, self.path)
        self.file_type = create_file_type(self.path, lst)
        self.inode = st.st_ino
        self.device = st.st_dev
        self.hard_link_count = st.st_nlink
        self.child_count = get_child_count(self.path, self.file_type.is_dir)
        self.symlink_target = get_symlink_target(self.path, self.file_type.is_symlink)

    def children(self) -> list[PathInfo] | None:
        """
        Get list of child PathInfo objects. This is always a live query, not cached.
        Returns None if not a directory or can't read.
        """
        if not self.file_type or not self.file_type.is_dir:
            return None
        try:
            return [PathInfo(child) for child in self.path.iterdir()]
        except (PermissionError, OSError):
            return None
