#!/usr/bin/env python

import os
import sys
import subprocess
import yaml


DRY_RUN = False


class AbortException(Exception):
    pass


class SkipException(Exception):
    pass


def rsync(args):
    print("rsync {}".format(" ".join(args)))
    if DRY_RUN:
        return

    ret = subprocess.call(["rsync"] + args)
    if ret != 0:
        raise AbortException("error executing rsync: {}".format(ret))


def ensure_dest(root, subpath):
    if not os.path.isdir(root):
        raise SkipException("error, dest path not present {}".format(root))
    final_path = os.path.join(root, subpath)
    if not os.path.isdir(final_path):
        print("mkdir -p {}".format(final_path))
        if not DRY_RUN:
            os.makedirs(final_path)


def add_leading_slash(path):
    if path.endswith("/"):
        return path
    else:
        return path + "/"


def backup(conf):
    try:
        for sub_src in conf.src_dirs:
            ensure_dest(conf.dest, sub_src)
            src = add_leading_slash(os.path.join(conf.src, sub_src))
            dest = add_leading_slash(os.path.join(conf.dest, sub_src))
            rsync(["-av", "--delete", src, dest])
        return True
    except SkipException as e:
        print("WARNING: skipping unavailable destination : {}"
              .format(conf.dest))
        return False


class BackupConf(object):
    def __init__(self, name, src, src_dirs, dest):
        self.name = name
        self.src = os.path.expanduser(src)
        self.src_dirs = src_dirs
        self.dest = os.path.expanduser(dest)


def parse_conf(path):
    with open(path) as f:
        conf = yaml.safe_load(f)
    result = []
    for b in conf["backups"]:
        result.append(BackupConf(b["name"], b["src"], b["srcDirs"], b["dest"]))
    return result


def dump_summary(summary):
    print("\n--- SUMMARY ---")
    for n, done in summary.items():
        print("{}: {}".format(n, "done" if done else "SKIPPED"))


def main():
    global DRY_RUN
    DRY_RUN = "--dry-run" in sys.argv
    try:
        conf_file = os.path.join(os.environ["HOME"], ".rsync-backup.yaml")
        conf = parse_conf(conf_file)

        summary = {}
        for backup_conf in conf:
            summary[backup_conf.name] = False

        for backup_conf in conf:
            print("Backup {}:".format(backup_conf.name))
            res = backup(backup_conf)
            summary[backup_conf.name] = res

        dump_summary(summary)

    except KeyboardInterrupt:
        print("ctrl-c received: aborted")
        dump_summary(summary)
    except Exception as e:
        print("Error executing backup: {}".format(e))


if __name__ == "__main__":
    main()
