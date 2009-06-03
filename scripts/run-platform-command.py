#!/usr/bin/env python

# First some configuration...
projectRepos = {
    "cellml-api": "http://www.bitbucket.org/a1kmm/cellml-api",
    "opencell": "http://www.bitbucket.org/a1kmm/opencell"
}

# For now... we need a better way to handle different branches.
snapshot_branch = 'trunk'

# Now the script proper...
import sys, os, shutil, mercurial, subprocess, re, datetime

def checked_call(cmd):
    print 'Executing ' + cmd
    if subprocess.call(cmd) != 0:
        print 'Error: ' + cmd + ' failed.'
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

repo = projectRepos[project]
configureOptions = ""
path = project + "-build"
java = False

if command == "test-java":
    path = project + "-java"
    command = "test"
    configureOptions = " --enable-java"

if command == "package-java":
    path = project + "-java"
    command = "package"
    java = True

mkPristine = not os.path.exists(project)

if deptype == "clobber":
    shutil.rmtree(path)
    fromPristine = True
else:
    fromPristine = not os.path.exists(path)

if not (command in ["package", "test"]):
    fail("Invalid command given to run-platform-command")

if cleanBuild and (command == "package"):
    fail("Must build and test successfully before package command can occur")

if command == "test":
    ui = mercurial.ui.ui()
    prisrepo = mercurial.hg.repository(ui, project)
    buildrepo = mercurial.hg.repository(ui, path)
    if mkPristine:
        mercurial.hg.clone(ui, repo, project, stream=None, rev=None,
                           pull=None, update=True)
    else:
        mercurial.hg.clean(prisrepo, None)
    
    if fromPristine:
        mercurial.hg.clone(ui, prisrepo, path, stream=None, rev=None, pull=None, update=True)
    else:
        mercurial.hg.clean(buildrepo, None)

    # Get the timestamp of this script...
    scriptTime = os.stat('./scripts/run-platform-command.py').st_mtime

    # We now have an up-to-date build repo, clobbered if requested. Build it...
    os.chdir(path)
    # To do: set up environment variables.

    if (not os.path.exists('Makefile')) or (os.stat('Makefile').st_mtime > scriptTime):
        checked_call(['./aclocal'])
        checked_call(['./autoconf'])
        checked_call(['./automake'])
        checked_call(['./configure'] + configureOptions)

    checked_call('make')
    checked_call('make check')
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
            if platform == 'linux-x86' or platform == 'linux-x86_64':
                spec = 'linux'
                xulrunner_path = '/data/mozilla_trunk/obj-i686-pc-linux-gnu/stablexr/dist'
                gsl = '/home/amil082/gsl-1.8/'
                xml_path = '/home/amil082/libxml2-2.6.27/'
                gcc_path = '/home/amil082/gcc-4.1.1/i686-pc-linux-gnu/'
                ship_gcc_path = '/home/amil082/gccprefix'
            checked_call(['./opencell/installers/FinalStageMaker.py', './opencell/installers/' + spec + '.spec',
                          'Mozilla=' + xulrunner_path + '/bin', 'OpenCell=./opencell', 'version=latest',
                          'CellMLAPI=./cellml-api', 'GSL=' + gsl_path,
                          'XML=' + xml_path, 'GCC=' + gcc_path,
                          'SHIPGCC=' + ship_gcc_path])
    os.chdir('/tmp/' + project)
    index = add_entry_to_index(open('index.html', 'r').read(), pathInSVN)
    open('index.html', 'w').write(index)
    
    checked_call('svn commit -m "Added a newly built snapshot"')
