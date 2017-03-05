#!/usr/bin/env python

"""Collection of generic tools.

These shouldn't be generally called by the modules."""

import os
import subprocess
import shlex
import collections
import re
import sys
import logging

import citadel.yaml


def run_cmd(cmd):
    """Run an arbitraty command, mixes STDERR with STDOUT."""
    proc = subprocess.Popen(
        shlex.split(cmd),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        universal_newlines=True)
    stdout, stderr = proc.communicate()
    return proc.returncode, stdout

def find_executable(executable):
    """Placeholder."""
    return executable

def ordered_load(stream, base_loader=citadel.yaml.Loader,
                 object_pairs_hook=collections.OrderedDict):
    """Load YAML file respecting appearance order."""
    class OrderedLoader(base_loader):
        """Placeholder."""
        pass
    def construct_mapping(loader, node):
        loader.flatten_mapping(node)
        return object_pairs_hook(loader.construct_pairs(node))
    OrderedLoader.add_constructor(
        citadel.yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
        construct_mapping)
    return citadel.yaml.load(stream, OrderedLoader)

def filter_secrets(lines):
    """Mask values whose key contains 'password'."""
    filtered = []
    for line in lines:
        if re.search('.*password.*', line, flags=re.IGNORECASE):
            subbed = re.sub(
                r'(password[\s:=]+)([\'"]*.*[\'"]*)[\s$].*',
                r'\1(*** hidden ***) ', line)
            filtered.append(subbed)
        elif re.search('.*secret.*', line, flags=re.IGNORECASE):
            subbed = re.sub(
                r'(secret[\s:=]+)([\'"]*.*[\'"]*)[\s$]',
                r'\1(*** hidden ***) ', line)
            filtered.append(subbed)
        else:
            filtered.append(line)
    return filtered

def find_downloader():
    """Look for a tool to download files with."""
    return """
DOWNLOADER=""
if which curl ; then
    DOWNLOADER="$(which curl) -O -s"
elif which wget ; then
    DOWNLOADER="$(which wget) -q"
else
    echo "Unable to find any downloader software. Aborting..." && exit 1
fi"""

def find_file(wildcard, variable='FILE'):
    """Look for an arbitraty file."""
    dirname = os.path.dirname(wildcard)
    if not dirname:
        dirname = '.'
    filename = os.path.basename(wildcard)
    return """%s=$(find %s -type f -name "%s")
if [ $(echo "$%s"  | wc -l) -gt 1 ] ; then
    echo "Too many results found while looking for %s. Aborting..." && exit 1
fi""" % (variable, dirname, filename, variable, wildcard)

def bash_syntax(string):
    """Validate string's compliance with bash syntax."""
    if not string:
        return False
    try:
        subprocess.check_call("echo '%s' | bash -n" % (string), shell=True)
        return True
    except subprocess.CalledProcessError:
        logging.debug(string)
        return False

def load_module(filename, path, classname=None):
    """Load a python module."""
    if not classname:
        classname = filename.capitalize()
    directory = os.path.dirname(path)
    if not directory in sys.path:
        sys.path.insert(0, directory)
    try:
        module = __import__(filename, globals(), locals(), [], -1)
        class_instance = getattr(module, classname)
        return class_instance
    except SyntaxError as exception:
        raise exception
    except ImportError as exception:
        print exception
        raise NotImplementedError("Unable to find requested module in path: %s" % (path))

def format_cmd(command_list):
    """Returns a nicely indented bash command."""
    return ' \\\n  '.join(command_list)
