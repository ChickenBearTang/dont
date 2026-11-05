"""테스트용 임시 PostgreSQL 서버. 서버 바이너리(initdb, pg_ctl)가 없으면 테스트를 건너뛴다.

유닉스 소켓만 열고(TCP 포트 없음) 임시 디렉터리에 데이터를 두며, 끝나면 지운다.
root 로 돌릴 때는 postgres 사용자로 실행한다 (postgres 는 root 로 뜨지 않는다).
"""

from __future__ import annotations

import glob
import itertools
import os
from pathlib import Path
import pwd
import shutil
import subprocess
import tempfile
import unittest


def _bin_dir() -> Path | None:
    for pattern in ("/usr/lib/postgresql/*/bin", "/usr/pgsql-*/bin", "/opt/homebrew/opt/postgresql*/bin"):
        for found in sorted(glob.glob(pattern), reverse=True):
            if (Path(found) / "initdb").exists() and (Path(found) / "pg_ctl").exists():
                return Path(found)
    which = shutil.which("initdb")
    return Path(which).parent if which and (Path(which).parent / "pg_ctl").exists() else None


def require_postgres() -> Path:
    try:
        import psycopg  # noqa: F401
    except ModuleNotFoundError as exc:
        raise unittest.SkipTest("psycopg 가 없어 PostgreSQL 테스트를 건너뛴다") from exc
    found = _bin_dir()
    if found is None:
        raise unittest.SkipTest("PostgreSQL 서버 바이너리(initdb/pg_ctl)가 없어 건너뛴다")
    return found


class TempPostgres:
    def __init__(self) -> None:
        self.bin = require_postgres()
        self._counter = itertools.count(1)
        self.root = Path(tempfile.mkdtemp(prefix="pgtest"))  # 소켓 경로 길이 제한 때문에 짧은 경로
        self._as_root = os.geteuid() == 0
        if self._as_root:
            user = pwd.getpwnam("postgres")
            os.chown(self.root, user.pw_uid, user.pw_gid)
            os.chmod(self.root, 0o700)
        self.data = self.root / "data"
        self.sock = self.root / "sock"
        self.sock.mkdir()
        if self._as_root:
            os.chown(self.sock, user.pw_uid, user.pw_gid)
        self.port = 54000 + os.getpid() % 900
        self._run("initdb", "-D", str(self.data), "-A", "trust", "-U", "test", "--no-sync", "-E", "UTF8", "--locale=C")
        try:
            self._run(
                "pg_ctl", "-D", str(self.data), "-w", "-l", str(self.root / "log"),
                "-o", f"-p {self.port} -k {self.sock} -c listen_addresses= -c fsync=off", "start",
            )
        except Exception:
            self.close()
            raise

    def _run(self, tool: str, *args: str) -> None:
        cmd = [str(self.bin / tool), *args]
        if self._as_root:
            cmd = ["runuser", "-u", "postgres", "--", *cmd]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        if result.returncode != 0:
            raise RuntimeError(f"{tool} 실패: {result.stdout}\n{result.stderr}")

    def _dsn(self, dbname: str) -> str:
        return f"host={self.sock} port={self.port} dbname={dbname} user=test"

    def new_database(self) -> str:
        """빈 데이터베이스를 하나 만들고 그 DSN 을 돌려준다 (테스트마다 새로)."""
        import psycopg

        name = f"t{next(self._counter)}"
        with psycopg.connect(self._dsn("postgres"), autocommit=True) as connection:
            connection.execute(f'CREATE DATABASE "{name}"')
        return self._dsn(name)

    def close(self) -> None:
        try:
            self._run("pg_ctl", "-D", str(self.data), "-m", "immediate", "-w", "stop")
        except Exception:
            pass
        shutil.rmtree(self.root, ignore_errors=True)
