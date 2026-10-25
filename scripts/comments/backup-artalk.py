"""为本机 Artalk 候选库创建一致性快照和私有配置备份，不停止服务。"""
import datetime
import hashlib
import os
import pathlib
import shutil
import sqlite3
import tarfile
from zoneinfo import ZoneInfo

os.umask(0o077)
root = pathlib.Path("/opt/artalk")
stamp = datetime.datetime.now(ZoneInfo("Asia/Shanghai")).strftime("%Y%m%d-%H%M%S")
backup = pathlib.Path("/opt/backups/dusklight-comments") / (stamp + "-artalk-candidate")
backup.mkdir(mode=0o700)
source = sqlite3.connect(f"file:{root}/data/artalk.db?mode=ro", uri=True)
destination = sqlite3.connect(backup / "artalk.db")
source.backup(destination)
assert destination.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
destination.close()
source.close()
for source_name, target in [
    ("data/artalk.yml", "runtime.private.yml"), ("production.private.yml", "production.private.yml"),
    ("admin.private.json", "admin.private.json"), ("compose.yml", "compose.yml"),
    ("rehearsal/image-digest.txt", "image-digest.txt"), ("rehearsal/legacy-map-final-verified.json", "legacy-map.json"),
    ("rehearsal/data-verification.json", "data-verification.json"), ("rehearsal/api-verification.json", "api-verification.json"),
    ("rehearsal/smtp-verification.json", "smtp-verification.json"), ("rehearsal/service-verification.json", "service-verification.json"),
    ("rehearsal/browser-verification.json", "browser-verification.json"),
]:
    shutil.copy2(root / source_name, backup / target)
for source_name, target in [
    (root / "oauth.private.json", "oauth.private.json"),
    (root / "origin-auth.private.json", "origin-auth.private.json"),
    (root / "rehearsal/historical-avatars.json", "historical-avatars.json"),
    (pathlib.Path("/opt/1panel/www/conf.d/artalk.mcxiaochen.top.conf"), "artalk-openresty.private.conf"),
    (pathlib.Path("/opt/1panel/www/conf.d/twikoo.mcxiaochen.top.conf"), "twikoo-openresty.private.conf"),
]:
    if source_name.exists():
        shutil.copy2(source_name, backup / target)
with (backup / "SHA256SUMS").open("x") as manifest:
    for file in sorted(backup.iterdir()):
        if file.name != "SHA256SUMS":
            manifest.write(hashlib.sha256(file.read_bytes()).hexdigest() + "  ./" + file.name + "\n")
archive = backup.with_suffix(".tar.gz")
with tarfile.open(archive, "x:gz") as tar:
    tar.add(backup, arcname=backup.name)
print("ARTALK_BACKUP=" + str(backup))
print("ARCHIVE_SHA256=" + hashlib.sha256(archive.read_bytes()).hexdigest())
