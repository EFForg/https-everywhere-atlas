#!/usr/bin/env python

import subprocess, os, sys, publicsuffix, pystache
from lxml import etree

HTTPS_E = "git://git.torproject.org/git/https-everywhere.git"
unstable_branch = "master"
stable_branch = "stable"

ps = publicsuffix.PublicSuffixList()

template = open("templates/domain.mustache").read()

stable_affected = {}
unstable_affected = {}

def clone_or_update():
    if os.path.isdir("https-everywhere"):
        os.chdir("https-everywhere/src/chrome/content/rules")
        unstable()
        result = subprocess.call(["git", "pull"])
        if result != 0:
            raise Exception, "Could not pull updates"
    else:
        result = subprocess.call(["git", "clone",  HTTPS_E])
        if result != 0:
            raise Exception, "Could not clone %s" % HTTPS_E

def stable():
    if subprocess.call(["git", "checkout", stable_branch]) != 0:
        raise Exception, "Could not switch to branch %s" % stable_branch

def unstable():
    if subprocess.call(["git", "checkout", unstable_branch]) != 0:
        raise Exception, "Could not switch to branch %s" % unstable_branch

def get_names(branch):
    if branch == stable_branch:
        affected = stable_affected
    else:
        affected = unstable_affected
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
                    host_data = (fi, name, dfo, unicode(etree.tostring(tree)).encode("utf-8"))
                    affected[host].append(host_data)
                    hosts.append(host)
                if dfo: out = "([file %s] %s  %s)"
                else: out = "[file %s] %s  %s"

clone_or_update()

sys.stderr.write("Checking unstable branch master:\n")
unstable()
get_names(unstable_branch)

sys.stderr.write("Checking stable branch %s:\n" % stable_branch)
stable()
get_names(stable_branch)

os.chdir("../../../../..")
for n in sorted(set(stable_affected.keys() + unstable_affected.keys())):
    d = {}
    d["domain"] = n
    d["affected_releases"] = ""
    d["stable_affected"] = False
    d["unstable_affected"] = False
    if n in stable_affected and n in unstable_affected:
        d["affected_releases"] = """The stable and development releases of HTTPS
                                 Everywhere currently rewrite requests to
                                 <b>%s</b> (or its subdomains).""" % n
    print "Domain", n
    if n in stable_affected:
        d["stable_affected"] = True
        if not d["affected_releases"]:
            d["affected_releases"] = """The stable release of HTTPS
                                     Everywhere currently rewrites requests to
                                     <b>%s</b> (or its subdomains).""" % n
        d["stable_enabled"] = []
        d["stable_disabled"] = []
        for effect in stable_affected[n]:
            fi, name, dfo, xml = effect
            if dfo:
                d["stable_disabled"].append({"rule_text": xml, "git_link": fi})
            else:
                d["stable_enabled"].append({"rule_text": xml, "git_link": fi})
#            print "\tBranch:", stable_branch
#            print "\tRuleset: %s   (%s)" % (name, fi)
#            if dfo: print "\tDEFAULT OFF"
#            print "\tXML: (%d bytes)" % len(xml)
#            print
        if d["stable_disabled"]: d["stable_has_disabled"] = True
        if d["stable_enabled"]: d["stable_has_enabled"] = True
    if n in unstable_affected:
        d["unstable_affected"] = True
        if not d["affected_releases"]:
            d["affected_releases"] = """The unstable release of HTTPS
                                     Everywhere currently rewrites requests to
                                     <b>%s</b> (or its subdomains).""" % n
        d["unstable_enabled"] = []
        d["unstable_disabled"] = []
        for effect in unstable_affected[n]:
            fi, name, dfo, xml = effect
            if dfo:
                d["unstable_disabled"].append({"rule_text": xml, "git_link": fi})
            else:
                d["unstable_enabled"].append({"rule_text": xml, "git_link": fi})
#            print "\tBranch:", unstable_branch
#            print "\tRuleset: %s   (%s)" % (name, fi)
#            if dfo: print "\tDEFAULT OFF"
#            print "\tXML: (%d bytes)" % len(xml)
#            print
        if d["unstable_disabled"]: d["unstable_has_disabled"] = True
        if d["unstable_enabled"]: d["unstable_has_enabled"] = True
    open("output/" + n + ".html", "w").write(pystache.render(template, d))
