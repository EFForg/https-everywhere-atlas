#!/usr/bin/env python

import subprocess, os, sys, publicsuffix
from lxml import etree

HTTPS_E = "git://git.torproject.org/git/https-everywhere.git"
unstable_branch = "master"
stable_branch = "3.0"

ps = publicsuffix.PublicSuffixList()

affected = {}

def stable():
    if subprocess.call(["git", "checkout", stable_branch]) != 0:
        raise Exception, "Could not switch to branch %s" % stable_branch

def unstable():
    if subprocess.call(["git", "checkout", unstable_branch]) != 0:
        raise Exception, "Could not switch to branch %s" % unstable_branch

def get_names(branch):
    for fi in sorted(os.listdir(".")):
        if fi[-4:] == ".xml":
            tree = etree.parse(fi)
            if tree.xpath("/ruleset"):
                dfo = bool(tree.xpath("/ruleset/@default_off"))
                name = tree.xpath("/ruleset/@name")[0]
                name = unicode(name).encode("utf-8")
                hosts = []
                for host in set(map(ps.get_public_suffix,  tree.xpath("/ruleset/target/@host"))):
                    host = unicode(host)
                    host = host.encode("idna")
                    if host == "*":
                        # This is a problem about wildcards at the end of
                        # target hosts.  Currently, we exclude such targets
                        # from having their own listings in the atlas.
                        continue
                    if host[:2] == "*.":
                        # A very small minority of rules apply to the entirety
                        # of something that the public suffix list considers
                        # a top-level domain, like blogspot.de (because every
                        # blogspot blog can perhaps be accessed via HTTPS, but
                        # individual users contrain the content of each
                        # subdomain).  In this unusual case, just list the
                        # higher level domain, without the *. part.
                        host = host[2:]
                    # print host
                    affected.setdefault(host, [])
                    host_data = (branch, fi, name, dfo, etree.tostring(tree))
                    affected[host].append(host_data)
                    hosts.append(host)
                if dfo: out = "([file %s] %s  %s)"
                else: out = "[file %s] %s  %s"

result = subprocess.call(["git", "clone",  HTTPS_E])

# TEMPORARILY don't actually require clone to succeed
# ... in the future, we will check whether we already
# have a checkout and do a git pull to update it!

# if result != 0:
#     raise Exception, "Could not clone %s" % HTTPS_E

os.chdir("https-everywhere/src/chrome/content/rules")

sys.stderr.write("Checking unstable branch master:\n")
unstable()
get_names(unstable_branch)

sys.stderr.write("Checking stable branch %s:\n" % stable_branch)
stable()
get_names(stable_branch)

for n in affected:
    print "Domain", n
    for effect in affected[n]:
        branch, fi, name, dfo, xml = effect
        print "\tBranch:", branch
        print "\tRuleset: %s   (%s)" % (name, fi)
        if dfo: print "\tDEFAULT OFF"
        print "\tXML: (%d bytes)" % len(xml)
        print
    print
