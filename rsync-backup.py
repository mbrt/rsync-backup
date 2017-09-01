#!/usr/bin/env python

import datetime as dt
import os
import sys
import subprocess
import yaml


DRY_RUN = False
BACKUP_STATE_VERSION = "v1"


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


def backup_section(conf):
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
    def __init__(self, name, every, src, src_dirs, dest):
        self.name = name
        self.every = every
        self.src = os.path.expanduser(src)
        self.src_dirs = src_dirs
        self.dest = os.path.expanduser(dest)


def parse_conf():
    path = path_to_conf("config.yaml")
    with open(path) as f:
        conf = yaml.safe_load(f)
    result = []
    for b in conf["backups"]:
        result.append(BackupConf(b["name"], b["everyDays"], b["src"],
                                 b["srcDirs"], b["dest"]))
    return result


def dump_summary(summary):
    print("\n--- SUMMARY ---")
    for n, done in summary.items():
        print("{}: {}".format(n, "done" if done else "SKIPPED"))


class BackupState(object):
    def __init__(self, conf=None):
        if conf is None:
            self.conf = {"version": BACKUP_STATE_VERSION, "backups": {}}
        else:
            self.conf = conf

    def write_to_file(self, path):
        with open(path, "w") as f:
            f.write(yaml.dump(self.conf))


def parse_backup_state():
    path = path_to_conf("state.yaml")
    try:
        with open(path) as f:
            conf = yaml.load(f)
    except:
        conf = None
    return BackupState(conf)


def write_backup_dates(state, summary):
    for name, done in summary.items():
        if done:
            section = {"lastBackup": dt.datetime.now()}
            state.conf["backups"][name] = section
    path = path_to_conf("state.yaml")
    state.write_to_file(path)


def path_to_conf(name):
    return os.path.join(os.environ["HOME"], ".rsync-backup", name)


def backup():
    try:
        conf = parse_conf()
        summary = {}

        for backup_conf in conf:
            summary[backup_conf.name] = False

        for c in conf:
            print("Backup {}:".format(c.name))
            res = backup_section(c)
            summary[c.name] = res

        dump_summary(summary)
        write_backup_dates(parse_backup_state(), summary)

    except KeyboardInterrupt:
        print("ctrl-c received: aborted")
        dump_summary(summary)
    except Exception as e:
        print("Error executing backup: {}".format(e))


def check_need_backup():
    try:
        state = parse_backup_state()
        conf = parse_conf()
        for c in conf:
            every = c.every
            s = state.conf["backups"].get(c.name, {})
            now = dt.datetime.now()
            if not s or s["lastBackup"] + dt.timedelta(days=every) < now:
                print("backup {} is outdated: need to backup now!"
                      .format(c.name))
    except Exception as e:
        print("Error checking backup state: {}".format(e))


def main():
    global DRY_RUN
    DRY_RUN = "--dry-run" in sys.argv
    if "--check-need-backup" in sys.argv:
        check_need_backup()
    else:
        backup()


if __name__ == "__main__":
    main()
