#!/bin/bash
mkpasswd -l |sed -e "s/\/home\//\/cygdrive\/c\/home\//" >/etc/passwd
export HOME=$(echo $HOME | sed -e "s/\/home\//\/cygdrive\/c\/home\//")
export B=/cygdrive/c/build
mkdir $B/downloads
wget http://go.microsoft.com/?linkid=7729279 -O $B/downloads/MSVC-CPP-Express-Setup.exe
chmod u+x $B/downloads/MSVC-CPP-Express-Setup.exe
echo <<END
About to install MSVC Expression Edition. Please do the following:
  * Choose Next on the first screen.
  * Select the first radio button on the next screen, and click next.
  * Unless you want them, disable SQL Server and Silverlight and click next.
  * Type 'c:\build\msvc9' in the Install In Folder box and click 'Install'.
  * Wait for the install to complete.
END
$B/downloads/MSVC-CPP-Express-Setup.exe
echo "Press any key to continue"
read

echo . $B/cellml-build/cygwin-build/msvc9-config >>~/.profile
. $B/cellml-build/cygwin-build/msvc9-config
wget http://download.microsoft.com/download/2/3/f/23f86204-39ee-4cd7-9a51-db19c9a8f8c4/Setup.exe -O $B/downloads/Windows-Platform-SDK-2008-Setup.exe
chmod u+x $B/downloads/Windows-Platform-SDK-2008-Setup.exe
echo <<END
About to install the Microsoft Platform SDK 2008. Please do the following:
  * Click Next
  * Click the first radio box and click next
  * In the first field, put c:\build\sdk
  * In the second field, put c:\build\sdk\samples
  * Click Next
  * In the next screen (tree view) you can turn off everything except "Windows Headers and Libraries" and "Windows Development Tools".
  * Click Next twice to start the download.
END
$B/downloads/Windows-Platform-SDK-2008-Setup.exe
echo "Press any key to continue"
read

cd /cygdrive/c/build
wget "http://downloads.sourceforge.net/project/omniorb/omniORB/omniORB-4.1.4/omniORB-4.1.4-x86_win32-vs9.zip?use_mirror=transact" -O omniORB-4.1.4-x86_win32-vs9.zip
unzip omniORB-4.1.4-x86_win32-vs9.zip
chmod -R u+x,g+x,o+x ./omniORB-4.1.4

# Set up our buildbot...
apt-cyg install python ed patch flex bison lapack subversion
cd /cygdrive/c/build
wget http://downloads.sourceforge.net/buildbot/buildbot-0.7.10p1.tar.gz
tar -xzf ./buildbot-0.7.10p1.tar.gz
cd ./buildbot-0.7.10p1
./setup.py install
cd ~
wget http://tmrc.mit.edu/mirror/twisted/Twisted/8.2/Twisted-8.2.0.tar.bz2
tar -xjf ./Twisted-8.2.0.tar.bz2 
cd Twisted-8.2.0
python setup.py install
cd ..
wget http://www.zope.org/Products/ZopeInterface/3.3.0/zope.interface-3.3.0.tar.gz
tar -xzf zope.interface-3.3.0.tar.gz
cd ./zope.interface-3.3.0
python setup.py install
cd ..
echo "Enter the password for the buildbot (displays on the screen)"
read PASSWORD
buildbot create-slave win32-buildslave autotest.bioeng.auckland.ac.nz:9989 msvc9-win32-a $PASSWORD
cd ./win32-buildslave
cp ./Makefile.sample ./Makefile
cd ./info
echo "Andrew Miller <ak.miller@auckland.ac.nz>" >info
echo "MSVC9 Windows build system" >host
cd ..
make
cd
wget http://releases.mozilla.org/pub/mozilla.org/xulrunner/releases/1.9.1.3/sdk/xulrunner-1.9.1.3.en-US.win32.sdk.zip
unzip ./xulrunner-1.9.1.3.en-US.win32.sdk.zip
# wget http://ftp.mozilla.org/pub/mozilla.org/xulrunner/nightly/2009-06-09-03-mozilla-central/xulrunner-1.9.2a1pre.en-US.win32.sdk.zip
# unzip ./xulrunner-1.9.2a1pre.en-US.win32.sdk.zip
chmod 0755 /cygdrive/c/build/xulrunner-sdk/bin/xpidl
chmod u+x /cygdrive/c/build/xulrunner-sdk/bin/xpt_link

for i in /cygdrive/c/build/xulrunner-sdk/bin/*.dll; do chmod u+x,g+x,o+x $i; cp $i /cygdrive/c/build/xulrunner-sdk/lib/`basename $i`; done

#wget http://www.alliedquotes.com/mirrors/gnu/gnu/gsl/gsl-1.12.tar.gz
#tar -xzf ./gsl-1.12.tar.gz
#cd ./gsl-1.12
#./configure --build=i686-win32-mingw32
#ed ./libtool <<EOF
#,s/max_cmd_len=/max_cmd_len=10000/
#w 
#q
#EOF
#make
# wget http://r2d3.geldreich.net/downloads/gsl-1.11-windows-binaries.zip

wget http://ftp.gnome.org/pub/GNOME/sources/libxml2/2.6/libxml2-2.6.30.tar.bz2
tar -xjf ./libxml2-2.6.30.tar.bz2
cd ./libxml2-2.6.30
patch -p0 <<END
--- ./include/win32config.h.old	2009-06-26 11:44:30.250000000 +1200
+++ ./include/win32config.h	2009-06-26 13:07:35.343750000 +1200
@@ -89,10 +89,12 @@
 #endif
 #endif /* _MSC_VER */
 
-#if defined(_MSC_VER) && (_MSC_VER < 1500)
+#if defined(_MSC_VER)
+#if (_MSC_VER < 1500)
 #define mkdir(p,m) _mkdir(p)
-#define snprintf _snprintf
 #define vsnprintf(b,c,f,a) _vsnprintf(b,c,f,a)
+#endif
+#define snprintf _snprintf
 #elif defined(__MINGW32__)
 #define mkdir(p,m) _mkdir(p)
 #endif
END
cd win32
ed ./Makefile.msvc <<EOF
,s/wsock32.lib/ws2_32.lib/
w
q
EOF
cscript.exe configure.js iconv=no
nmake
cp ./bin.msvc/libxml2.lib /cygdrive/c/build/msvc9/VC/lib/xml2.lib
cp ./bin.msvc/libxml2.dll /cygdrive/c/WINDOWS/system32/xml2.dll
cd /cygdrive/c/build/
wget "http://downloads.sourceforge.net/sourceforge/cppunit/cppunit-1.12.1.tar.gz?use_mirror=transact" -O cppunit-1.12.1.tar.gz
tar -xzf ./cppunit-1.12.1.tar.gz
cd ./cppunit-1.12.1
echo MSVC will now come up - go to Build => Batch Build, build cppunit debug and release, then quit MSVC and press enter when complete.
/cygdrive/c/build/msvc9/Common7/IDE/VCExpress.exe src\\CppUnitLibraries.dsw
read
cp lib/cppunit*.lib /cygdrive/c/build/msvc9/VC/lib/
cp -R include/cppunit /cygdrive/c/build/msvc9/VC/include/
mkdir /cygdrive/c/bin
cp /bin/sh.exe /cygdrive/c/bin/sh.exe
cp /usr/include/FlexLexer.h /cygdrive/c/build/msvc9/VC/include/
cd /cygdrive/c/build
wget "http://downloads.sourceforge.net/sourceforge/nsis/nsis-2.45-setup.exe?use_mirror=transact" -O nsis-2.45-setup.exe
echo "Running NSIS setup. Follow through the prompts and do a default install"
chmod u+x ./nsis-2.45-setup.exe
mkdir /cygdrive/c/localcache

mkdir /cygdrive/c/build/redist
cd /cygdrive/c/build/redist
wget http://download.microsoft.com/download/1/1/1/1116b75a-9ec3-481a-a3c8-1777b5381140/vcredist_x86.exe
