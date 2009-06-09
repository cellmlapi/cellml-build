#!/usr/bin/env python

# First some configuration...
projectRepos = {
    "cellml-api": "http://cellml-api.hg.sourceforge.net/hgroot/cellml-api",
    "opencell": "http://cellml-opencell.hg.sourceforge.net/hgroot/cellml-opencell"
}

# For now... we need a better way to handle different branches.
snapshot_branch = 'trunk'

# Now the script proper...
import sys, os, shutil, mercurial, mercurial.ui, mercurial.hg, mercurial.commands, subprocess, re, datetime

def checked_call(cmd):
    print 'Executing ' + cmd[0]
    if subprocess.call(cmd) != 0:
        print 'Error: ' + cmd[0] + ' failed.'
        sys.exit(1)

def fail(why):
    print why
    sys.exit(1)

def build_new_entry(path):
    newrev = int((re.search('Revision: ([0-9]+)',
                            subprocess.Popen(['svn', 'info'],
                                             stdout=subprocess.PIPE).stdout.read())).
                 group(1)) + 1
    date = datetime.datetime.today().strftime('%Y-%m-%d %H:%M')
    url = 'https://svn.physiomeproject.org/svn/physiome/!svn/bc/%u/%s' % (newrev, path)
    return '<a href="%s">%s</a>' % (url, date)

def add_entry_to_index(index, path):
    index.replace('<!-- New entries go here -->',
                  '<li>' + build_new_entry(path) +\
                  "</li>\n<!-- New entries go here -->")

# Get the platform.
uname = subprocess.Popen(['uname', '-a'], stdout=subprocess.PIPE).stdout.read()
if re.search('mingw32', os.getcwd()):
    platform = 'mingw32'
elif re.search('CYGWIN', uname) != None:
    platform = 'win32'
elif re.search('Linux .*86 ', uname) != None:
    platform = 'linux-x86'
elif re.search('Linux .*86_64 ', uname) != None:
    platform = 'linux-x86_64'
elif re.search('Darwin.*86 ', uname) != None:
    platform = 'osx-x86'
else:
    platform = 'unknown'

project = sys.argv[1]
command = sys.argv[2]
deptype = sys.argv[3]

if platform == 'linux-x86' or platform == 'linux-x86_64':
    spec = 'linux'
    xulrunner_path = '/data/mozilla_trunk/obj-i686-pc-linux-gnu/stablexr/dist'
    gsl = '/home/amil082/gsl-1.8/'
    xml_path = '/home/amil082/libxml2-2.6.27/'
    gcc_path = '/home/amil082/gcc-4.1.1/i686-pc-linux-gnu/'
    ship_gcc_path = '/home/amil082/gccprefix'

repo = projectRepos[project]
if project == "cellml-api":
    configureOptions = ["--enable-xpcom=" + xulrunner_path, "--enable-context",
                        "--enable-annotools", "--enable-cuses",
                        "--enable-cevas", "--enable-vacss",
                        "--enable-malaes", "--enable-ccgs",
                        "--enable-celeds", "--enable-cis",
                        "--enable-rdf"]
else:
    configureOptions = ["--with-mozilla=" + xulrunner_path,
                        "--with-cellml_api=" + os.getcwd().replace('build_opencell', 'build_api') + '/../cellml-api-build']
path = project + "-build"
java = False

# Get the timestamp of this script...
scriptTime = os.stat('./scripts/run-platform-command.py').st_mtime

if command == "test-java":
    path = project + "-java"
    command = "test"
    configureOptions += ["--enable-java"]

if command == "package-java":
    path = project + "-java"
    command = "package"
    java = True

mkPristine = not os.path.exists('../' + project)

if deptype == "clobber":
    try:
        shutil.rmtree('../' + path)
    except OSError:
        pass
    fromPristine = True
else:
    fromPristine = not os.path.exists('../' + path)

if not (command in ["package", "test"]):
    fail("Invalid command given to run-platform-command")

if fromPristine and (command == "package"):
    fail("Must build and test successfully before package command can occur")

os.chdir('..')

if command == "test":
    ui = mercurial.ui.ui()
    if mkPristine:
        mercurial.hg.clone(ui, repo, project, stream=None, rev=None,
                           pull=None, update=True)
        prisrepo = mercurial.hg.repository(ui, project)
    else:
        prisrepo = mercurial.hg.repository(ui, project)
        mercurial.commands.pull(ui, prisrepo, repo,
                                update=True)
    
    if fromPristine:
        mercurial.hg.clone(ui, prisrepo, path, stream=None, rev=None, pull=None, update=True)
        buildrepo = mercurial.hg.repository(ui, path)
    else:
        buildrepo = mercurial.hg.repository(ui, path)
        mercurial.commands.pull(ui, buildrepo, project, update=True)

    # We now have an up-to-date build repo, clobbered if requested. Build it...
    os.chdir(path)
    # To do: set up environment variables.

    if (not os.path.exists('Makefile')) or (os.stat('Makefile').st_mtime > scriptTime):
        checked_call(['aclocal'])
        checked_call(['autoconf'])
        checked_call(['automake'])
        checked_call(['./configure'] + configureOptions)

    checked_call(['make'])
    checked_call(['make', 'check'])
elif command == "package":
    if project == "cellml-api":
        # Source code only...
        platform = ""
    
    checked_call(['svn', 'co', 'https://svn.physiomeproject.org/svn/physiome/snapshots/' +\
                  project + '/' + snapshot_branch + '/' + platform, '/tmp/' + project + platform])
    
    pathInSVN = 'snapshots/' + project + '/' + snapshot_branch + '/'
    if project == 'cellml-api':
        checked_call(['tar', '--exclude=.hg', '-cjf', '/tmp/' + project + '/cellml-api.tar.bz2',
                      project])
        pathInSVN += "cellml-api.tar.bz2"
    elif java:
        pass
    elif project == "opencell":
        if platform == "win32":
            checked_call(["c:\\Program Files\\NSIS\\makensis.exe", "opencell-win32.nsi"])
        else:
            cellml_api = os.getcwd().replace('build_opencell', 'build_api') + '/../cellml-api-build'
            checked_call(['./opencell-build/installers/FinalStageMaker.py', './opencell-build/installers/' + spec + '.spec',
                          'Mozilla=' + xulrunner_path + '/bin', 'OpenCell=./opencell-build', 'version=latest',
                          'CellMLAPI=' + cellml_api, 'GSL=' + gsl_path,
                          'XML=' + xml_path, 'GCC=' + gcc_path,
                          'SHIPGCC=' + ship_gcc_path])
    os.chdir('/tmp/' + project)
    index = add_entry_to_index(open('index.html', 'r').read(), pathInSVN)
    open('index.html', 'w').write(index)
    
    checked_call(['svn', 'commit', '-m', 'Added a newly built snapshot'])
