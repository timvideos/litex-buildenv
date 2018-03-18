#!/usr/bin/env python3

import argparse
import csv
import os
import pprint
import sys
import tempfile
import urllib.request

import subprocess

slug = os.getenv("TRAVIS_REPO_SLUG", None)
prebuilt_repo_name = 'HDMI2USB-firmware-prebuilt'
if slug:
    prebuilt_repo_owner = slug.split('/',1)[0]
else:
    prebuilt_repo_owner = None

parser = argparse.ArgumentParser(
    description="""\
Update the index files in the prebuilt repo.""")
parser.add_argument(
    '--repo', default=prebuilt_repo_name)
parser.add_argument(
    '--owner', default=prebuilt_repo_owner)
parser.add_argument(
    '--branch', default=os.getenv('TRAVIS_BRANCH', None))
parser.add_argument(
    '--full-platform', default=os.getenv('FULL_PLATFORM', None))
parser.add_argument(
    '--target', default=os.getenv('TARGET', None))
parser.add_argument(
    '--full-cpu', default=os.getenv('FULL_CPU', None))
parser.add_argument(
    '--firmware', default=os.getenv('FIRMWARE', None))
parser.add_argument(
    '--gh-user', default=os.getenv('GH_USER', None))
parser.add_argument(
    '--gh-token', default=os.getenv('GH_TOKEN', None))
parser.add_argument(
    '--outdir', default=os.getenv('OUTDIR', None))
args = parser.parse_args()

assert args.repo
assert args.owner
assert args.branch == "master"

assert args.gh_user
assert args.gh_token

assert args.full_platform
assert args.target
assert args.full_cpu

svn_base_url = "https://github.com/{}/{}/trunk/archive/{}".format(
    args.owner, args.repo, args.branch)
pre_base_url = "https://github.com/{}/{}/branches/gh-pages".format(
    args.owner, args.repo, args.branch)

git_dir_url = "https://github.com/{}/{}/blob/master/archive/{}".format(
    args.owner, args.repo, args.branch)
git_file_url = "https://github.com/{}/{}/blob/master/archive/{}".format(
    args.owner, args.repo, args.branch)

svn_args = '--non-interactive --username {} --password {}'.format(
    args.gh_user, args.gh_token)

print()
print("Looking at cpu '{}' in target '{}' for platform '{}' from '{}/{}'".format(
    args.full_cpu, args.target, args.full_platform, args.owner, args.repo))
print()
print("-"*75)
print()

revs_data = subprocess.check_output(
    "svn list {} {}".format(svn_args, svn_base_url).split()).decode('utf-8')

revs = [v[:-1] for v in revs_data.splitlines()]
def parse_version(v):
    if "-" not in v:
        return v,0,''
    a,b,c = v.split('-')
    return a,int(b),c
revs.sort(key=parse_version)

def get_channel_spreadsheet():
    data = urllib.request.urlopen(
        "https://docs.google.com/spreadsheets/d/e/2PACX-1vTmqEM-XXPW4oHrJMD7QrCeKOiq1CPng9skQravspmEmaCt04Kz4lTlQLFTyQyJhcjqzCc--eO2f11x/pub?output=csv"
    ).read().decode('utf-8')

    rev_names = {}
    for i in csv.reader(data.splitlines(), dialect='excel'):
        if not i:
            continue
        if i[0] != "GitHub":
            continue

        _, _, rev, name, conf, *_ = i
        if not name:
            continue
        assert name not in rev_names, "{} is listed multiple times!".format(
            name)
        rev_names[name] = rev

    return rev_names

_get_sha256sum_cache = {}
def get_sha256sum(rev, full_platform, target, full_cpu, svn_args=svn_args, svn_base_url=svn_base_url):
    global _get_sha256sum_cache
    full_path = "{rev}/{full_platform}/{target}/{full_cpu}/".format(
        rev=rev,
        full_platform=full_platform,
        target=target,
        full_cpu=full_cpu,
    )
    try:
        return _get_sha256sum_cache[full_path]
    except KeyError:
        try:
            data = subprocess.check_output(
                "svn cat {svn_args} {svn_base_url}/{full_path}/sha256sum.txt".format(
                    svn_args=svn_args,
                    svn_base_url=svn_base_url,
                    full_path=full_path,
                ).split(),
                stderr=subprocess.STDOUT,
            ).decode('utf-8')
            data = data.replace("./", "{}/{}".format(git_file_url, full_path))
        except subprocess.CalledProcessError:
            print("  - Did not find {full_platform}/{target}/{full_cpu} at {rev}".format(
                rev=rev,
                full_platform=full_platform,
                target=target,
                full_cpu=full_cpu,
            ))
            data = None
        _get_sha256sum_cache[full_path] = data
        return data

channels = {}

# Find the unstable revision
print("Found {} revisions, 10 latest:\n  * ".format(len(revs)), end="")
print("\n  * ".join(reversed(revs[-10:])))
urevs = list(revs)
while True:
    rev = urevs.pop(-1)
    if not get_sha256sum(rev, args.full_platform, args.target, args.full_cpu):
        continue
    channels['unstable'] = rev
    break
print()

# Get the stable/testing revisions
print("Getting other channels..")
channels.update(get_channel_spreadsheet())

# Get the sha254 files for each channel
output = {}
for channel, rev in sorted(channels.items()):
    output[channel] = get_sha256sum(
        rev, args.full_platform, args.target, args.full_cpu)
print()

for channel, rev in sorted(channels.items()):
    if not output[channel]:
        rev = "unknown"
    print("Channel {:10s} is at rev {}".format(channel, rev))
print()

# Download the gh-pages branch of the HDMI2USB-firmware-prebuilt repo
if args.outdir is None:
    tmpdir = tempfile.mkdtemp()
else:
    tmpdir = args.outdir

os.makedirs(tmpdir, exist_ok=True)
print("Using {}".format(tmpdir))
print()

os.chdir(tmpdir)
print("Download github pages repo...")
if not os.path.exists("gh-pages"):
    subprocess.check_call(
        "svn checkout {} -q {}".format(svn_args, pre_base_url).split())
print("Done.")
print("")
os.chdir("gh-pages")

with open("revs.txt", "w") as f:
    for rev in revs:
        f.write("{}\n".format(rev))

out_dir = os.path.join(args.full_platform, args.target, args.full_cpu)
os.makedirs(out_dir, exist_ok=True)

with open(os.path.join(out_dir, "channels.txt"), "w") as f:
    for channel, rev in sorted(channels.items()):
        gh_url = "{git_base_url}/{rev}/{full_platform}/{target}/{full_cpu}/".format(
            git_base_url=git_dir_url,
            rev=rev,
            full_platform=args.full_platform,
            target=args.target,
            full_cpu=args.full_cpu)
        f.write("{} {} {}\n".format(channel, rev, gh_url))

for channel, lines in sorted(output.items()):
    if not lines:
        continue
    with open(os.path.join(out_dir, "{}.sha256sum".format(channel)), "w") as f:
        f.write("".join(lines))

all_files = []
for root, dirs, files in os.walk('.'):
    skip_dirs = []
    for d in dirs:
        if d.startswith('.'):
            skip_dirs.append(d)
    for d in skip_dirs:
        dirs.remove(d)
    for f in files:
        if f == 'index.txt':
            continue
        all_files.append(os.path.join(root, f))

all_files.sort()

with open('index.txt', 'w') as f:
    subprocess.check_call(["sha256sum"]+all_files, stdout=f)

print("Adding files...")
subprocess.check_call(["svn", "add", "--parents", "--force"]+all_files)
subprocess.check_call(["svn", "add", "--parents", "--force", "index.txt"])
print()

print("Current status...")
changes = subprocess.check_output("svn status -u --depth infinity".split(), stderr=subprocess.STDOUT).decode('utf-8')
print(changes)
subprocess.check_call("svn diff .".split(), stderr=subprocess.STDOUT)
print()

if len(changes.splitlines()) == 1:
    print("No changes to commit...")
    print()
else:
    print()
    print("Committing changes...")

    with tempfile.NamedTemporaryFile() as f:
        f.write("Updating channels (in Travis build {})\n".format(os.getenv("TRAVIS_BUILD_NUMBER", "None")).encode('utf-8'))
        f.flush()

        subprocess.check_call("svn commit {} --file {}".format(svn_args, f.name).split())

print()
print("-"*75)
print("Done..")
print()
