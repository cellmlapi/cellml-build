#!/usr/bin/env python

# First some configuration...
projectRepos = {
    "cellml-api": 
"http://cellml-api.hg.sourceforge.net/hgroot/cellml-api/cellml-api",
}
projectVersions = {
    "cellml-api": "1.9",
}
projectRevisions = {
    "cellml-api":  None
}
projectTrunk = {
    "cellml-api": True
}
# Which platform is responsible for packaging up the source code?
packageSourceOn = {
    "cellml-api": "linux-x86"
}


# Now the script proper...
import sys, time, os, shutil, mercurial, mercurial.ui, mercurial.hg, mercurial.commands, subprocess, re, datetime, string
from mercurial.node import hex

def checked_call(cmd, filterout="alloweverything"):
    print 'Executing ' + string.join(cmd, ' ')
    docmd = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    outfilter = subprocess.Popen(['grep', '-vE', filterout], stdin=docmd.stdout)
    errfilter = subprocess.Popen(['grep', '-vE', filterout], stdin=docmd.stderr)
    while True:
        if outfilter.poll() != None and errfilter.poll() != None and docmd.poll() != None:
            break
        time.sleep(0.1)
    if docmd.returncode != 0:
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

if len(sys.argv) < 4:
    print "run-platform-command.py [project] [command] [clobber|depend][,valgrind]"
    quit()

project = sys.argv[1]
command = sys.argv[2]
options = sys.argv[3].split(',')

def firstWithDefault(f, d, x):
    l = filter(f, x)
    if len(l) == 0:
        return d
    else:
        return l.pop()

deptype = firstWithDefault(lambda x: x == "clobber" or x == "depend", "depend", options)
testtype = firstWithDefault(lambda x: x == "rawcpu" or x == "valgrind", "rawcpu", options)

static = 0

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
version = projectVersions[project]

if project == "cellml-api":
    configureOptions = ["--enable-xpcom=" + xulrunner_path,
                        "--enable-java", "--enable-python",
                        "--enable-context",
                        "--enable-annotools", "--enable-cuses",
                        "--enable-cevas", "--enable-vacss",
                        "--enable-malaes", "--enable-ccgs",
                        "--enable-celeds", "--enable-cis",
                        "--enable-rdf",    "--enable-telicems",
                        "--enable-spros"]
    if platform in ['linux-x86', 'linux-x86_64', 'osx-x86']:
        configureOptions.append('--enable-gsl-integrators')

path = project + "-build"

# Get the timestamp of this script...
scriptTime = os.stat('./scripts/run-platform-command.py').st_mtime

os.chdir('..')

if command == "build-static":
    path = project + "-static"
    command = "test"
    static = 1
    configureOptions += ["--enable-static"]
    configureOptions += ["--disable-shared"]
    configureOptions += ["--enable-examples=no"]
    configureOptions.remove('--enable-context')
    configureOptions.remove("--enable-xpcom=" + xulrunner_path)

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
        mercurial.hg.clone(ui, repo, project, stream=None,
                           pull=None, update=True, rev=None)
        prisrepo = mercurial.hg.repository(ui, project)
    else:
        prisrepo = mercurial.hg.repository(ui, project)
        mercurial.commands.pull(ui, prisrepo, repo,
                                update=True, force=None, rev=None)
    
    print ("Pristine repository tip: %s" % hex(prisrepo.filectx(prisrepo, '.').node()))
        
    if fromPristine:
        mercurial.hg.clone(ui, project, path, stream=None, rev=None, pull=None, update=True)
        buildrepo = mercurial.hg.repository(ui, path)
    else:
        buildrepo = mercurial.hg.repository(ui, path)
        mercurial.commands.pull(ui, buildrepo, project, update=True, force=None, rev=None)
    if projectRevisions[project] != None:
      mercurial.commands.update(ui, buildrepo, rev=projectRevisions[project], clean=True)
    else:
      mercurial.commands.update(ui, buildrepo, rev=None if projectTrunk[project] else version, clean=True)
    print "Build repository current branch: "
    mercurial.commands.branch(ui, buildrepo)
    #print ("Build repository current status: ")
    #mercurial.commands.status(ui, buildrepo)


    # We now have an up-to-date build repo, clobbered if requested. Build it...
    os.chdir(path)
    # To do: set up environment variables.

    os.environ['CFLAGS'] = os.environ['CXXFLAGS'] = os.environ['LDFLAGS'] = '-O2'

    if (not os.path.exists('Makefile')) or (os.stat('Makefile').st_mtime < scriptTime):
        checked_call(['aclocal'], 'libIDL.m4')
        checked_call(['autoconf'])
        checked_call(['automake'])
        checked_call(['./configure'] + configureOptions)

    checked_call(['make'], "LAPACK not available|WIN32.*macro redefinition|unsafe mix.*bool.*PRBool|yywrap.*Already defined|Directory component ignored|locally defined symbol|LNK4088|checking for undefined symbols may be affected|xulrunner-sdk.*Current.*does not exist|No debug map|libtool.*seems to be moved|sundials.*C470")
    if static == 0:
        if testtype == "rawcpu":
            checked_call(['make', 'check'], 'WIN32.*macro redefinition|xulrunner-sdk.*Current.*does not exist')
        else:
            checked_call(['make', 'check', 'TESTS_ENVIRONMENT=./tests/ValgrindWrapper'], 'WIN32.*macro redefinition|xulrunner-sdk.*Current.*does not exist')
        checked_call(['make', 'cellml-sdk.tar.bz2'])
elif command == "package":
    finalPart = ''

    try:
        shutil.rmtree('/tmp/' + project + platform)
    except OSError:
        pass

    versionBranch = 'branches/' + version

    packagingSourceHere = packageSourceOn[project] == platform
    
    if packagingSourceHere:
      pathInSVN = 'snapshots/' + project + '/' + versionBranch + '/source/'
      checked_call(['svn', 'co', 'https://svn.physiomeproject.org/svn/physiome/' +\
                    pathInSVN, '/tmp/' + project + "source"])

      if project == "cellml-api":
          cellml_api_source = os.getcwd().replace('package_api', 'clean_build_api') + ''

      if project == 'cellml-api':
        os.chdir(cellml_api_source + '/cellml-api')
        checked_call(['aclocal'])
        checked_call(['automake'])
        checked_call(['autoconf'])
        checked_call(['tar', '--exclude=.hg', '-cjf', '/tmp/' + project + '/cellml-api-' + version + '.tar.bz2',
                      '-C', cellml_api_source, project])
        finalPart = "cellml-api.tar.bz2"

      pathInSVN += finalPart
    
      os.chdir('/tmp/' + project + "source")
      checked_call(['svn', 'up', '/tmp/' + project + platform])
      index = add_entry_to_index(open('index.html', 'r').read(), pathInSVN)
      open('index.html', 'w').write(index)
      # Add the program, in case this is the first invocation on this branch.
      checked_call(['svn', 'add', finalPart])
      checked_call(['svn', 'commit', '-m', 'Added a newly built source snapshot'])

    pathInSVN = 'snapshots/' + project + '/' + versionBranch + '/' + platform + '/'
    checked_call(['svn', 'co', 'https://svn.physiomeproject.org/svn/physiome/' +\
                  pathInSVN, '/tmp/' + project + platform])
    os.chdir('/tmp/' + project + platform)

    if project == 'cellml-api':
        # This needs to be updated to specify the specific files to include on each platform.
        cellml_api_built = os.getcwd().replace('package_api', 'clean_build_api') + '/cellml-api-build'
        finalPart = 'cellml-sdk.tar.bz2'
        checked_call(['cp', cellml_api_built + '/cellml-sdk.tar.bz2', '/tmp/' + project + '/' +
                      finalPart])

    pathInSVN += finalPart
    
    checked_call(['svn', 'up', '/tmp/' + project + platform])
    index = add_entry_to_index(open('index.html', 'r').read(), pathInSVN)
    open('index.html', 'w').write(index)
    # Add the program, in case this is the first invocation on this branch.
    checked_call(['svn', 'add', finalPart])
    checked_call(['svn', 'commit', '-m', 'Added a newly built snapshot'])
