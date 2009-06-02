#!/usr/bin/env python

# First some configuration...
projectRepos =
{
    "cellml-api": "http://www.bitbucket.org/a1kmm/cellml-api",
    "opencell": "http://www.bitbucket.org/a1kmm/opencell"
}

# Now the script proper...
import sys, os, shutil, mercurial

def fail(why):
    print why
    sys.exit(1)

project = sys.argv[1]
command = sys.argv[2]
deptype = sys.argv[3]

repo = projectRepos[project]
extraConfigureOptions = ""
path = project

if command == "test-java":
    path = project + "-java"
    command = "test"
    extraConfigureOptions = " --enable-java"

if command == "package-java":
    path = project + "-java"
    command = "package"

if deptype == "clobber":
    shutil.rmtree(path)
    cleanBuild = True
else:
    cleanBuild = not os.path.exists(project)

if not (command in ["package", "test"]):
    fail("Invalid command given to run-platform-command")

if cleanBuild and (command == "package"):
    fail("Must build and test successfully before package command can occur")

if command == "test":
    ui = mercurial.ui.ui()
    hrepo = mercurial.hg.repository(ui, repo)
    if cleanBuild:
        mercurial.hg.clone(ui, repo, project, rev=None, pull=None, )
    else:
        

if cleanBuild:
    mercurial.commands.checkout

print "To do: On project %s, do %s with dependency type %s" % (project, command, deptype)
