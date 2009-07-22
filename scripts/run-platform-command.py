#!/usr/bin/env python

# First some configuration...
projectRepos = {
    "cellml-api": "http://cellml-api.hg.sourceforge.net/hgroot/cellml-api",
    "opencell": "http://cellml-opencell.hg.sourceforge.net/hgroot/cellml-opencell"
}

# For now... we need a better way to handle different branches.
snapshot_branch = 'trunk'

# Now the script proper...
import sys, os, shutil, mercurial, mercurial.ui, mercurial.hg, mercurial.commands, subprocess, re, datetime, string

def checked_call(cmd):
    print 'Executing ' + string.join(cmd, ' ')
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
    return index.replace('<!-- New entries go here -->',
                         '<li>' + build_new_entry(path) +\
                         "</li>\n<!-- New entries go here -->")

def toNative(cpath):
    if cpath[0] != '/':
        return cpath.replace('/', '\\')
    if cpath[0:10] == '/cygdrive/':
        return cpath[10] + ':\\' + cpath[12:].replace('/', '\\')
    return 'c:\\cygwin' + cpath.replace('/', '\\')

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
    xulrunner_path = '/home/autotest/xulrunner-sdk'
    gsl_path = '/home/autotest/gsl-1.8/'
    xml_path = '/home/autotest/libxml2-2.6.27/'
    gcc_path = '/home/autotest/gcc-4.1.1/i686-pc-linux-gnu/'
    ship_gcc_path = '/home/autotest/gccprefix'
elif platform == 'win32':
    xulrunner_path = '/cygdrive/c/build/xulrunner-sdk'
    gsl_path = 'c:\\build\\gsl\\'
    xml_path = 'c:\\build\libxml2\\'
    gcc_path = 'c:\\build\\gcc'
    ship_gcc_path = 'c:\\build\\gcc-prefix'
elif platform == 'osx-x86':
    spec = 'osx'
    xulrunner_path = '/sw/xulrunner-sdk'
    gsl_path = '/Users/cmiss/Build/gsl-1.8'
    xml_path = ''
    gcc_path = ''
    ship_gcc_path = ''

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

os.chdir('..')

if command == "test-java":
    path = project + "-java"
    command = "test"
    configureOptions += ["--enable-java"]
    configureOptions.remove('--enable-context')

if command == "package-java":
    path = project + "-java"
    command = "package"
    java = True

mkPristine = not os.path.exists(project)

if deptype == "clobber":
    try:
        shutil.rmtree(path)
    except OSError:
        pass
    fromPristine = True
else:
    fromPristine = not os.path.exists(os.getcwd().replace('package_', 'clean_build_') + '/' + path)

if not (command in ["package", "test"]):
    fail("Invalid command given to run-platform-command")

if fromPristine and (command == "package"):
    fail("Must build and test successfully before package command can occur")

if command == "test":
    ui = mercurial.ui.ui()
    if mkPristine:
        mercurial.hg.clone(ui, repo, project, stream=None, rev=None,
                           pull=None, update=True)
        prisrepo = mercurial.hg.repository(ui, project)
    else:
        prisrepo = mercurial.hg.repository(ui, project)
        mercurial.commands.pull(ui, prisrepo, repo,
                                update=True, rev=None, force=None)
    
    if fromPristine:
        mercurial.hg.clone(ui, project, path, stream=None, rev=None, pull=None, update=True)
        buildrepo = mercurial.hg.repository(ui, path)
    else:
        buildrepo = mercurial.hg.repository(ui, path)
        mercurial.commands.pull(ui, buildrepo, project, update=True, rev=None, force=None)

    # We now have an up-to-date build repo, clobbered if requested. Build it...
    os.chdir(path)
    # To do: set up environment variables.

    os.environ['CFLAGS'] = os.environ['CXXFLAGS'] = os.environ['LDFLAGS'] = '-O2'

    if (not os.path.exists('Makefile')) or (os.stat('Makefile').st_mtime < scriptTime):
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

    if project == "cellml-api":
        cellml_api = os.getcwd().replace('package_api', 'clean_build_api')
    else:
        cellml_api = os.getcwd().replace('package_opencell', 'clean_build_api') + '/cellml-api-build'
        opencell = os.getcwd().replace('package_opencell', 'clean_build_opencell') + '/opencell-build'

    pathInSVN = 'snapshots/' + project + '/' + snapshot_branch + '/'

    os.chdir('/tmp/' + project + platform)
    if project == 'cellml-api':
        checked_call(['tar', '--exclude=.hg', '-cjf', '/tmp/' + project + '/cellml-api.tar.bz2',
                      '-C', cellml_api, project])
        pathInSVN += "cellml-api.tar.bz2"
    elif java:
        pass
    elif project == "opencell":
        pathInSVN += platform + "/"
        if platform == "win32":
            checked_call(["cl", "/Fo" + toNative(opencell + "/appSupport/win32/opencell"), toNative(opencell + "/appSupport/win32/launcher-win32.c")])
            checked_call(["/cygdrive/c/Program Files/NSIS/makensis", toNative(opencell + "/installers/opencell-win32.nsi")])
            pathInSVN += "opencell.exe"
        else:
            checked_call([opencell + '/installers/FinalStageMaker.py', opencell + '/installers/' + spec + '.spec',
                          'Mozilla=' + xulrunner_path + '/bin', 'OpenCell=' + opencell, 'version=latest',
                          'CellMLAPI=' + cellml_api, 'GSL=' + gsl_path,
                          'XML=' + xml_path, 'GCC=' + gcc_path,
                          'SHIPGCC=' + ship_gcc_path])
            if platform == "linux-x86":
                pathInSVN += "opencell-x86_Linux.tar.bz2"
            elif platform == "osx-x86":
                pathInSVN += "opencell-i386_OSX.dmg"
    index = add_entry_to_index(open('index.html', 'r').read(), pathInSVN)
    open('index.html', 'w').write(index)
    
    checked_call(['svn', 'commit', '-m', 'Added a newly built snapshot'])
