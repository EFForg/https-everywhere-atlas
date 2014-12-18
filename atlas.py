#!/usr/bin/env python

import subprocess, os, sys, publicsuffix, inspect

# make it so we can import python modules directly from this git repo
# http://stackoverflow.com/questions/279237/python-import-a-module-from-a-folder
cmd_subfolder = os.path.realpath(os.path.abspath(os.path.join(os.path.split(inspect.getfile( inspect.currentframe() ))[0],"python_modules")))
if cmd_subfolder not in sys.path:
    sys.path.insert(0, cmd_subfolder)

import pystache
from lxml import etree

HTTPS_E = "https://git.torproject.org/git/https-everywhere.git"
unstable_branch = "master"
stable_branch = "3.0"

ps = publicsuffix.PublicSuffixList()

index_template = open("templates/index.mustache").read()
letter_template = open("templates/letter.mustache").read()
domain_template = open("templates/domain.mustache").read()
redirect_template = open("templates/redirect.mustache").read()

stable_affected = {}
unstable_affected = {}

def clone_or_update():
    if os.path.isdir("https-everywhere"):
        os.chdir("https-everywhere/src/chrome/content/rules")
        unstable()
        result = subprocess.call(["git", "pull", "-q"])
        if result != 0:
            raise Exception, "Could not pull updates"
    else:
        result = subprocess.call(["git", "clone",  HTTPS_E])
        if result != 0:
            raise Exception, "Could not clone %s" % HTTPS_E

def stable():
    if subprocess.call(["git", "checkout", "-q", stable_branch]) != 0:
        raise Exception, "Could not switch to branch %s" % stable_branch
    if subprocess.call(["git", "merge", "-q", "origin/" + stable_branch]) != 0:
        raise Exception, "Could not merge from origin on branch %s" % stable_branch
    return subprocess.Popen(["git", "log", "-1", "--pretty=format:%h %ai"], stdout=subprocess.PIPE, stderr=None).stdout.read()

def unstable():
    if subprocess.call(["git", "checkout", "-q", unstable_branch]) != 0:
        raise Exception, "Could not switch to branch %s" % unstable_branch
    if subprocess.call(["git", "merge", "-q", "origin/" + unstable_branch]) != 0:
        raise Exception, "Could not merge from origin on branch %s" % unstable_branch
    return subprocess.Popen(["git", "log", "-1", "--pretty=format:%h %ai"], stdout=subprocess.PIPE, stderr=None).stdout.read()

def get_names(branch):
    if branch == stable_branch:
        affected = stable_affected
    else:
        affected = unstable_affected
    for fi in sorted(os.listdir(".")):
        if fi[-4:] == ".xml":
            try:
                tree = etree.parse(fi)
            except:
                # Parsing this ruleset failed for some reason.
                continue
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
                    affected.setdefault(host, [])
                    host_data = (unicode(fi, "utf-8"), name, dfo, unicode(etree.tostring(tree)).encode("utf-8"))
                    affected[host].append(host_data)
                    hosts.append(host)
                if dfo: out = "([file %s] %s  %s)"
                else: out = "[file %s] %s  %s"

clone_or_update()

# sys.stderr.write("Checking unstable branch master:\n")
unstable_as_of = unstable()
get_names(unstable_branch)

# sys.stderr.write("Checking stable branch %s:\n" % stable_branch)
stable_as_of = stable()
get_names(stable_branch)

os.chdir("../../../../..")

domains = sorted(set(stable_affected.keys() + unstable_affected.keys()))

first_letters_list = sorted(set(n[0] for n in domains))
first_letters = []
for l in first_letters_list:
    first_letters.append({ 'letter': l })
output = pystache.render(index_template, { 'letters': first_letters, 'domains': domains})
open("output/index.html", "w").write(output.encode("utf-8"))

def letter_domain_pairs(domains):
    last_letter = domains[0][0]
    domains_index = []
    for n in domains:
        if n[0] != last_letter:
            yield last_letter, domains_index
            last_letter = n[0]
            domains_index = []
        domains_index.append({ 'domain': n})
    yield last_letter, domains_index

redirect_output = pystache.render(redirect_template, { 'redirect': '../' })

if not os.path.exists('output/domains'):
    os.mkdir('output/domains')
open("output/domains/index.html", "w").write(redirect_output.encode("utf-8"))

if not os.path.exists('output/letters'):
    os.mkdir('output/letters')
open("output/letters/index.html", "w").write(redirect_output.encode("utf-8"))

for letter, domains_index in letter_domain_pairs(domains):
    output = pystache.render(letter_template, { 'letters': first_letters,
                                                'first_letter': letter,
                                                'domains': domains_index })
    open("output/letters/%s.html" % letter, "w").write(output.encode("utf-8"))

for n in domains:
    d = {}
    d["stable_as_of"] = stable_as_of
    d["unstable_as_of"] = unstable_as_of
    d["domain"] = n
    d["affected_releases"] = ""
    d["stable_affected"] = False
    d["unstable_affected"] = False
    if n in stable_affected and n in unstable_affected:
        d["affected_releases"] = """The stable and development releases of
                      <a href="https://www.eff.org/https-everywhere">HTTPS
                      Everywhere</a> currently rewrite requests to
                      <b>%s</b> (or its subdomains). Millions of browsers
                      will be affected by these rewrites.""" % n
    if n in stable_affected:
        d["stable_affected"] = True
        if not d["affected_releases"]:
            d["affected_releases"] = """The stable release of
                      <a href="https://www.eff.org/https-everywhere">HTTPS
                      Everywhere</a> currently rewrites requests to
                      <b>%s</b> (or its subdomains). Millions of browsers
                      will be affected by these rewrites.""" % n
        d["stable_enabled"] = []
        d["stable_disabled"] = []
        for effect in stable_affected[n]:
            fi, name, dfo, xml = effect
            if dfo:
                d["stable_disabled"].append({"rule_text": xml, "git_link": fi})
            else:
                d["stable_enabled"].append({"rule_text": xml, "git_link": fi})
        if d["stable_disabled"]: d["stable_has_disabled"] = True
        if d["stable_enabled"]: d["stable_has_enabled"] = True
    if n in unstable_affected:
        d["unstable_affected"] = True
        if not d["affected_releases"]:
            d["affected_releases"] = """The development release of
                      <a href="https://www.eff.org/https-everywhere">HTTPS
                      Everywhere</a> currently rewrites requests to
                      <b>%s</b> (or its subdomains). In the future,
                      millions of users will be affected by these
                      rewrites.""" % n
        d["unstable_enabled"] = []
        d["unstable_disabled"] = []
        for effect in unstable_affected[n]:
            fi, name, dfo, xml = effect
            if dfo:
                d["unstable_disabled"].append({"rule_text": xml, "git_link": fi})
            else:
                d["unstable_enabled"].append({"rule_text": xml, "git_link": fi})
        if d["unstable_disabled"]: d["unstable_has_disabled"] = True
        if d["unstable_enabled"]: d["unstable_has_enabled"] = True

    output = pystache.render(domain_template, d)
    open("output/domains/" + n + ".html", "w").write(output.encode("utf-8"))
