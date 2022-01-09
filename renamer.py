#!env python3

import re, os, sys, glob
import argparse
from string import Formatter as Fmt
from typing import Sequence, Mapping, Any
class Formatter(Fmt):
    """https://docs.python.org/3.10/library/string.html#string.Formatter"""
    def get_field(self, field_name: str, args: Sequence[Any], kwargs: Mapping[str, Any]) -> Any:
        obj, used_key = super().get_field(field_name, args, kwargs)
        if callable(obj):
            obj = obj()
        return (obj, used_key)
    
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--doit", default=False, action="store_true", help="Do It!!")
    parser.add_argument("-m", "--mkdir", default=False, action="store_true", help="Make dirs")
    parser.add_argument("-rx", "--regex", help="regex")
    parser.add_argument("-o", "--out", help="output filename template")
    parser.add_argument("files", nargs="*", help="files to rename")
    parser.add_argument("--frame1", default=False, action="store_true", help="start from frame 1")
    parser.add_argument("--seq", default=False, action="store_true", help="renumber sequentially")
    parser.add_argument("-v", "--verbose", action="store_true", default=False)
    parser.add_argument("-s", "--strict", action="store_true", default=False)
    args = parser.parse_args()

    strict = args.strict
    doit = args.doit
    mkdir = args.mkdir
    verbose = args.verbose
    fmt = Formatter()
    if args.regex:
        regex = re.compile(args.regex)
    elif os.path.isfile("renamer.regex"):
        with open("renamer.regex") as rxfile:
            regex = re.compile(rxfile.read(), re.VERBOSE)
    else:
        parser.error("No regex given")

    if args.out:
        filepat = args.out
    elif os.path.isfile("renamer.format"):
        with open("renamer.format") as fmtfile:
            for line in fmtfile:
                line = line.strip()
                if line[0] == "#":
                    continue
                elif line:
                    filepat = line
                    break
    else:
        parser.error("No output format string given")

    if args.files:
        infiles = args.files
    else:
        infiles = glob.glob("*")

    pairs = []
    files = {}
    frames = {}
    ins, outs = set(), set()
    for name in infiles:
        srch = regex.search(name)
        if not srch:
            if strict:
                print(f"non-matching filename: \"{name}\"", file=sys.stderr)
            continue

        if name in ins:
            continue
        if not os.path.exists(name):
            print(f"WARNING: Source file does not exist! (\"{name}\")", file=sys.stderr)
            continue

        files[name] = srch
        frames[name] = int(srch.group('frame'))
        ins.add(name)
    if frames:
        if args.frame1:
            if args.seq:
                renum = {orig: new for new, orig in enumerate(sorted(set(frames.values())), 1)}
                frames = {name: renum[frame] for name, frame in frames.items()}
            else:
                minframe = min(frames.values())
                frames = {name: fnum-minframe+1 for name, fnum in frames.items()}

    for name in infiles:
        if name in outs:
            print(f"WARNING: Source Filename collision! (\"{name}\")", file=sys.stderr)
            continue

        if name in frames:
            info = dict(files[name].groupdict(), frame=frames[name], env=os.environ)
        else:
            info = dict(files[name].groupdict(), env=os.environ)
        newname = fmt.vformat(filepat, (), info)

        if newname in outs:
            print(f"ERROR: Dest Filename collision! (\"{name}\" => \"{newname}\")", file=sys.stderr)
            sys.exit(1)
        if os.path.exists(newname):
            print(f"ERROR: Dest filename already exists! (\"{name}\" => \"{newname}\")", file=sys.stderr)
            sys.exit(1)

        pairs.append((name, newname))
        outs.add(newname)

    if not pairs:
        print("Nothing to do...", file=sys.stderr)
        sys.exit(1)

    maxin = max(map(len, ins))
    for name, newname in pairs:
        dirname = os.path.dirname(newname)
        if dirname and not os.path.isdir(dirname):
            if mkdir:
                if (not doit) or verbose:
                    print(f"mkdir: \"{dirname}\"")
                if doit:
                    os.makedirs(dirname)
            else:
                print(f"ERROR: Destination path doesn't exist! \"{dirname}\"", file=sys.stderr)
                sys.exit(1)
        if (not doit) or verbose:
            print(f"\"{name}\"".ljust(maxin+2) + f" => \"{newname}\"")
        if doit:
            os.rename(name, newname)
