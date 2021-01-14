#!env python3

import re, os, sys, glob
import argparse

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--doit", default=False, action="store_true", help="Do It!!")
    parser.add_argument("-m", "--mkdir", default=False, action="store_true", help="Make dirs")
    parser.add_argument("-rx", "--regex", help="regex")
    parser.add_argument("-o", "--out", help="output filename template")
    parser.add_argument("files", nargs="*", help="files to rename")
    parser.add_argument("-v", "--verbose", action="store_true", default=False)
    parser.add_argument("-s", "--strict", action="store_true", default=False)
    args = parser.parse_args()

    strict = args.strict
    doit = args.doit
    mkdir = args.mkdir
    verbose = args.verbose
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
            filepat = fmtfile.read().strip()
    else:
        parser.error("No output format string given")
    
    if args.files:
        infiles = args.files
    else:
        infiles = glob.glob("*")

    pairs = []
    ins, outs = set(), set()
    for name in infiles:
        srch = regex.search(name)
        if not srch:
            if strict:
                print(f"non-matching filename: \"{name}\"", file=sys.stderr)
            continue
 
        if name in ins:
            continue
        if name in outs:
            print(f"WARNING: Source Filename collision! (\"{name}\")", file=sys.stderr)
            continue
        if not os.path.exists(name):
            print(f"WARNING: Source file does not exist! (\"{name}\")", file=sys.stderr)
            continue

        newname = filepat.format(**srch.groupdict(), env=os.environ)
        if newname in outs:
            print(f"ERROR: Dest Filename collision! (\"{newname}\")", file=sys.stderr)
            sys.exit(1)
        if os.path.exists(newname):
            print(f"ERROR: Dest filename already exists! (\"{newname}\")", file=sys.stderr)
            sys.exit(1)

        pairs.append((name, newname))
        ins.add(name)
        outs.add(newname)
    
    if not pairs:
        print("No files matched...", file=sys.stderr)
        sys.exit(1)

    maxin = max(map(len, ins))
    for name, newname in pairs:
        dir = os.path.dirname(newname)
        if not os.path.isdir(dir):
            if mkdir:
                if (not doit) or verbose:
                    print(f"mkdir: \"{dir}\"")
                if doit:
                    os.makedirs(dir)
            else:
                print(f"ERROR: Destination path doesn't exist! \"{dir}\"", file=sys.stderr)
                sys.exit(1)
        if (not doit) or verbose:
            print(f"\"{name}\"".ljust(maxin+2) + f" => \"{newname}\"")
        if doit:
            os.rename(name, newname)
