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
echo . $B/physiome-build/cygwin-build/msvc9-config >>~/.bashrc
. $B/physiome-build/cygwin-build/msvc9-config
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

# Set up our buildbot...
apt-cyg install python
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
cd ..
wget http://ftp.mozilla.org/pub/mozilla.org/xulrunner/nightly/2009-06-09-03-mozilla-central/xulrunner-1.9.2a1pre.en-US.win32.sdk.zip
unzip ./xulrunner-1.9.2a1pre.en-US.win32.sdk.zip
wget http://www.alliedquotes.com/mirrors/gnu/gnu/gsl/gsl-1.12.tar.gz
tar -xzf ./gsl-1.12.tar.gz
cd ./gsl-1.12
./configure && make
