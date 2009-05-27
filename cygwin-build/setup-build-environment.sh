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
