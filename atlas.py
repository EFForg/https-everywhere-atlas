#!/usr/bin/env python

import subprocess, os, sys, publicsuffix, inspect, json, shutil, re, pystache
from lxml import etree

HTTPS_E = "https://github.com/EFForg/https-everywhere.git"
release_branch = "release"
stable_branch = "master"

ps = publicsuffix.PublicSuffixList()

index_template = open("templates/index.mustache").read()
letter_template = open("templates/letter.mustache").read()
ruleset_template = open("templates/ruleset.mustache").read()
redirect_template = open("templates/redirect.mustache").read()

domain_rulesets = {}

stable_rulesets = {}
release_rulesets = {}

renderer = pystache.Renderer(string_encoding='utf-8')

def clone_or_update():
    if os.path.isdir("https-everywhere"):
        os.chdir("https-everywhere/src/chrome/content/rules")
        stable()
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

def release():
    if subprocess.call(["git", "checkout", "-q", release_branch]) != 0:
        raise Exception, "Could not switch to branch %s" % release_branch
    if subprocess.call(["git", "merge", "-q", "origin/" + release_branch]) != 0:
        raise Exception, "Could not merge from origin on branch %s" % release_branch
    return subprocess.Popen(["git", "log", "-1", "--pretty=format:%h %ai"], stdout=subprocess.PIPE, stderr=None).stdout.read()

def public_suffix_wrapper(domain):
    if re.match("^([0-9]{1,3}\.){3}[0-9]{1,3}$", domain):
        return domain
    else:
        return ps.get_public_suffix(domain)

def get_names(branch):
    if branch == stable_branch:
        rulesets = stable_rulesets
    else:
        rulesets = release_rulesets
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
                filename = unicode(fi, "utf-8")

                current_ruleset = [name, dfo, etree.tostring(tree, encoding='utf-8')]
                rulesets[filename] = current_ruleset

                for host in set(map(public_suffix_wrapper,  tree.xpath("/ruleset/target/@host"))):
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

                    domain_rulesets.setdefault(host, set())
                    domain_rulesets[host].add(filename)

                    rulesets.setdefault(filename, [])
                    rulesets[filename].append(host)

                if dfo: out = "([file %s] %s  %s)"
                else: out = "[file %s] %s  %s"

clone_or_update()

release_as_of = release()
get_names(release_branch)

stable_as_of = stable()
get_names(stable_branch)

os.chdir("../../../../..")

def hosts_to_filenames(host):
    rulesets_for_host = len(domain_rulesets[host])
    if rulesets_for_host != 1:
        return [host + '-' + str(current) for current in range(1, rulesets_for_host + 1)]
    else:
        return [host]

domains_nested = map(hosts_to_filenames, sorted(domain_rulesets.keys()))
domains = [item for sublist in domains_nested for item in sublist]

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

if os.path.exists('output/domains'):
    shutil.rmtree("output/domains")
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

for domain in domain_rulesets:
    if len(domain_rulesets[domain]) > 1:
        num = 1
        for ruleset_filename in domain_rulesets[domain]:
            os.symlink("../rulesets/" + ruleset_filename + ".html", "output/domains/" + domain + "-" + str(num) + ".html")
            num += 1
    else:
        os.symlink("../rulesets/" + domain_rulesets[domain].pop() + ".html", "output/domains/" + domain + ".html")

if not os.path.exists('output/rulesets'):
    os.mkdir('output/rulesets')

for ruleset in set(stable_rulesets.keys() + release_rulesets.keys()):
    d = {}
    d["stable_as_of"] = stable_as_of
    d["release_as_of"] = release_as_of
    d["stable_affected"] = False
    d["release_affected"] = False
    d["stable_hosts"] = []
    d["release_hosts"] = []

    if ruleset in stable_rulesets:
        d["stable_hosts"] = json.dumps(stable_rulesets[ruleset][3:])
        name, dfo, xml = stable_rulesets[ruleset][:3]
        d["stable_enabled"] = False
        d["stable_disabled"] = False
        if dfo:
            d["stable_disabled"] = {"rule_text": xml, "git_link": ruleset}
        else:
            d["stable_enabled"] = {"rule_text": xml, "git_link": ruleset}
        if d["stable_disabled"]: d["stable_has_disabled"] = True
        if d["stable_enabled"]: d["stable_has_enabled"] = True
    if ruleset in release_rulesets:
        d["release_hosts"] = json.dumps(release_rulesets[ruleset][3:])
        name, dfo, xml = release_rulesets[ruleset][:3]
        d["release_enabled"] = False
        d["release_disabled"] = False
        if dfo:
            d["release_disabled"] = {"rule_text": xml, "git_link": ruleset}
        else:
            d["release_enabled"] = {"rule_text": xml, "git_link": ruleset}
        if d["release_disabled"]: d["release_has_disabled"] = True
        if d["release_enabled"]: d["release_has_enabled"] = True

    d['stable_branch'] = stable_branch
    d['release_branch'] = release_branch

    output = renderer.render(ruleset_template, d)
    open("output/rulesets/" + ruleset + ".html", "w").write(output.encode("utf-8"))
