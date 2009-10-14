class Installerpage
  def initialize(text, buttons)
    @text = text
    @buttons = buttons
  end
  attr_reader :text, :buttons
end

module Dwnldmgr
  def walk_dependancies(all, dependancies, done)
    debug "All"
    debug all.join(", ")
    all.compact!
    if all == nil 
      return done
    end
    all.each do |package|
      debug package.to_s
      unless ([package] - done == [])
        if dependancies[package] == nil
          done.push package
          debug "Pushing package"
          debug done.join(", ")
        else
          if (dependancies[package] - done) == []
            done.push package
            debug "Pushing package"
            debug done.join(", ")
          else
            debug "recursing"
            done = walk_dependancies(dependancies[package], dependancies, done)
            unless ([package] - done == [])
              done.push package
              debug "Post recurse, pushing package"
              debug done.join(", ")
            end
          end
        end
      end
    end
    debug "Done"
    debug done.join(", ")
    return done
  end
  def path_string
    [File.join(@installdir['msvc9'], "Common7\\IDE").to_s, File.join(@installdir['msvc9'], "VC\\bin").to_s, File.join(@installdir['msvc9'], "Common7\\Tools").to_s, File.join(@installdir['msvc9'], "VC\\VCPackages").to_s, File.join(@installdir['omniorb'], "omniORB-4.1.4/bin/x86_win32/"), "%PATH%" ].join(';')
  end
  def native_to_cygwin path 
    # We use cygwin to do our conversion for us
    run_cmd "set TRANSLATION=#{path} && #{File.join(@installdir['cygwin'], '\bin\bash.exe')} -login -c 'echo $TRANSLATION'"
  end
  def run_cmd(command, suppress_output=true)
    pipe = IO::popen 'cmd.exe', 'r+'
    pipe.puts command
    pipe.close_write
    buf = pipe.read
    pipe.close_read
    status = $?.exitstatus
    para "Failed" + command +"\n" unless status == 0 or suppress_output == true
    buf
  end
  def run_cmd_path command
    run_cmd "set PATH=" + path_string + "\r\n" + command
  end
  def msvc9_config
    @msvc_hash = {'@PATH' => path_string, '@physiomebuild' => @installdir['physiome-build'], '@cygwinmountpoint' => @installdir['cygwin'],
    '@buildroot' => @installdir['physiome-build'] }
    @msvc9_out = File.open("#{File.join(@installdir['physiome-build'], 'physiome-build/msvc-build/msvc9-config')}", 'w')
    @msvc9_in = File.open("#{File.join(@installdir['physiome-build'], 'physiome-build/msvc-build/msvc9-config.in')}", 'r')
    @msvc9_in.readlines.each { |line| 
      @msvc9_out.put line.gsub(/@[a-zA-Z]/) do |match|
        @msvc_hash[match]
      end
    }
    @msvc9_out.close
    
  end
  def makepage page 
    @currentstack.hide if @currentstack != nil
    @currentstack = stack do
      page.text.call
      page.buttons.each do |name, action|
        button name do
          makepage @pagesfinal[action]
        end
      end
    end   
  end
  def projectpage
    @projects.map! do |project|
      flow { @c = check; para project }
      [project, @c]
    end

  end
  
end

Shoes.app :title => "Setup Physiome build environment" do
  background "#eee"
  extend Dwnldmgr
  @packages = ['cygwin', 'apt-cyg', 'cygwin-packages', 'msvc9', 'windowsplatformsdk', 'omniorb', 'xulrunner', 'java-sdk', 'libxml2', 'physiome-build', 'cellml-api-source', 'opencell-source', 'mingw']
  @dependancies = {
    'apt-cyg' => ['cygwin'], 'windowsplatformsdk' => ['msvc9'],
    'omniorb' => ['windowsplatformsdk', 'apt-cyg', 'cygwin'], 'xulrunner' => ['apt-cyg', 'cygwin'],
    'cygwin-packages' => ['apt-cyg'], 'libxml2' => ['windowsplatformsdk', 'cygwin', 'cygwin-packages'],
    'physiome-build' => ['cygwin', 'apt-cyg', 'cygwin-packages'],
    'cppunit' => ['windowsplatformsdk', 'apt-cyg', 'msvc9', 'cygwin-packages'],
    'cellml-api-source' => ['windowsplatformsdk', 'cygwin', 'cygwin-packages', 'omniorb', 'cppunit'],
    'opencell-source' => ['windowsplatformsdk', 'cygwin', 'cygwin-packages', 'cellml-api-source', 'mingw']
  }
  @projects = ['CellML API', 'CellML API Java Bindings', 'Physiome Buildbot', 'OpenCell', 'Build scripts']
  @project2package = {
    'CellML API' => ['cellml-api-source', 'cygwin', 'apt-cyg', 'cygwin-packages', 'msvc9', 'windowsplatformsdk', 'omniorb', 'xulrunner', 'libxml2', 'cppunit'],
    'CellML API Java Bindings' => ['cellml-api-source', 'cygwin', 'apt-cyg', 'cygwin-packages', 'msvc9', 'windowsplatformsdk', 'omniorb', 'javasdk', 'libxml2', 'cppunit'],
    'Build scripts' => ['physiome-build'],
    'OpenCell' => ['cellml-api-source', 'cygwin', 'apt-cyg', 'cygwin-packages', 'msvc9', 'windowsplatformsdk', 'omniorb', 'xulrunner', 'libxml2', 'cppunit', 'opencell-source']
  }
  @url = {
    'cygwin'             => "http://www.cygwin.com/setup.exe",
    'apt-cyg'            => "http://stephenjungels.com/jungels.net/projects/apt-cyg/apt-cyg",
    'msvc9'              => "http://go.microsoft.com/?linkid=7729279",
    'windowsplatformsdk' => "http://download.microsoft.com/download/2/3/f/23f86204-39ee-4cd7-9a51-db19c9a8f8c4/Setup.exe",
    'omniorb'            => "http://downloads.sourceforge.net/project/omniorb/omniORB/omniORB-4.1.4/omniORB-4.1.4-x86_win32-vs9.zip?use_mirror=transact",
    'xulrunner'          => "http://releases.mozilla.org/pub/mozilla.org/xulrunner/releases/1.9.1.3/sdk/xulrunner-1.9.1.3.en-US.win32.sdk.zip",
    'libxml2'            => "http://ftp.gnome.org/pub/GNOME/sources/libxml2/2.6/libxml2-2.6.30.tar.bz2",
    'cppunit'            => "http://downloads.sourceforge.net/sourceforge/cppunit/cppunit-1.12.1.tar.gz?use_mirror=transact"
  }
  @localpackage = {
    'cygwin'             => "setup.exe",
    'apt-cyg'            => "apt-cyg",
    'msvc9'              => "MSVC-CPP-Express-Setup.exe",
    'windowsplatformsdk' => "Windows-Platform-SDK-2008-Setup.exe",
    'omniorb'            => "omniORB-4.1.4-x86_win32-vs9.zip",
    'xulrunner'          => "xulrunner-1.9.1.3.en-US.win32.sdk.zip",
    'libxml2'            => "libxml2-2.6.30.tar.bz2",
    'cppunit'            => "cppunit-1.12.1.tar.gz"
  }
  @packagedir = {
    'cygwin'             => "c:\\Downloads",
    'apt-cyg'            => "c:\\Downloads",
    'msvc9'              => "c:\\Downloads",
    'windowsplatformsdk' => "c:\\Downloads",
    'omniorb'            => "c:\\Downloads",
    'xulrunner'          => "c:\\Downloads",
    'libxml2'            => "c:\\Downloads",
    'cppunit'            => "c:\\Downloads"
  }
  @installdir = {
    'cygwin'             => "c:\\cygwin",
    'apt-cyg'            => "c:\\cygwin\\bin",
    'msvc9'              => "c:\\build\\msvc9",
    'windowsplatformsdk' => "c:\\build\\sdk",
    'omniorb'            => "c:\\build\\omniORB-4.1.4",
    'xulrunner'          => "c:\\build",
    'libxml2'            => "c:\\build",
    'physiome-build'     => "c:\\build\\physiome-build",
    'cppunit'            => "c:\\build\\cppunit",
    'cygwin-packages'    => "c:\\cygwin",
    'cellml-api-source'  => "c:\\build",
    'opencell-source'    => "c:\\build"
  } 
  @installhook = {
    'cygwin'             => lambda { File.new(File.join(@packagedir["cygwin"], @localpackage["cygwin"])).chmod(777)
                                     `#{File.join(@packagedir["cygwin"], @localpackage["cygwin"]).to_s}`
                                     para "Cygwin installed\n"  },
    'cygwin-packages'    => lambda { #para run_cmd_path "#{File.join(@installdir["cygwin"], "bin\\bash.exe")} -login -c \"cd ~ && apt-cyg update && apt-cyg install python mercurial zip unzip tar ed flex bison lapack subversion patch && echo Done\""
                                     system("#{File.join(@installdir["cygwin"], "bin\\bash.exe")} -login -c \"apt-cyg install python mercurial zip unzip tar ed flex bison lapack subversion patch\"")
                                     para "\n"
                                     para "Cygwin packages installed\n" },
    'apt-cyg'            => lambda { `copy #{File.join(@packagedir["apt-cyg"], @localpackage["apt-cyg"]).to_s} #{@installdir["apt-cyg"]} `
                                     para "apt-cyg installed\n" },
    'omniorb'            => lambda { `#{File.join(@installdir["cygwin"], "bin\\bash.exe")} -login -c "cd /cygdrive/c/ && cp Downloads/omniORB-4.1.4-x86_win32-vs9.zip build/omniORB-4.1.4-x86_win32-vs9.zip && cd build && unzip omniORB-4.1.4-x86_win32-vs9.zip && chmod -R u+x,g+x,o+x ./omniORB-4.1.4"`
                                     para "Omniorb installed\n" },
    'xulrunner'          => lambda { system("#{File.join(@installdir['cygwin'], 'bin\\bash.exe')} -login -c \"pwd && cd \`cygpath --unix #{@installdir['xulrunner']}\` && pwd && echo \`cygpath --unix #{@packagedir['xulrunner']}\`/#{@localpackage['xulrunner']} && cp \`cygpath --unix #{@packagedir['xulrunner']}\`/#{@localpackage['xulrunner']} ./#{@localpackage['xulrunner']} && unzip #{@localpackage['xulrunner']} && chmod 0755 xulrunner-sdk/bin/xpidl && chmod u+x xulrunner-sdk/bin/xpt_link && for i in xulrunner-sdk/bin/*.dll; do cp $i xulrunner-sdk/lib/\`basename $i\`; done\"")
                                     para "Xulrunner installed\n" },
    'msvc9'              => lambda { `#{File.join(@packagedir["msvc9"], @localpackage["msvc9"]).to_s}`
                                     # Add directories to PATH
                                     
                                      },
    'windowsplatformsdk' => lambda { `#{File.join(@packagedir["windowsplatformsdk"], @localpackage["windowsplatformsdk"]).to_s}` },
    'libxml2'            => lambda { system("#{File.join(@installdir['cygwin'], 'bin\\bash.exe')} -login -c 'cd #{@installdir['libxml2']} && tar -xjf ./libxml2-2.6.30.tar.bz2 && cd ./libxml2-2.6.30 && patch -p0 <<END
--- ./include/win32config.h.old	2009-06-26 11:44:30.250000000 +1200
+++ ./include/win32config.h	2009-06-26 13:07:35.343750000 +1200
@@ -90,10 +90,12 @@
 #endif /* _MSC_VER */
 
 #if defined(_MSC_VER)
+#if (_MSC_VER < 1500)
 #define mkdir(p,m) _mkdir(p)
-#define snprintf _snprintf
 #define vsnprintf(b,c,f,a) _vsnprintf(b,c,f,a)
+#endif
+#define snprintf _snprintf
 #elif defined(__MINGW32__)
 #define mkdir(p,m) _mkdir(p)
 #endif
END && cd win32 && ed ./Makefile.msvc <<EOF
,s/wsock32.lib/ws2_32.lib/
w
q
EOF && cscript.exe configure.js iconv=no && nmake && cp ./bin.msvc/libxml2.lib /cygdrive/c/build/msvc9/VC/lib/xml2.lib && cp ./bin.msvc/libxml2.dll /cygdrive/c/WINDOWS/system32/xml2.dll'") },
    'physiome-build'     => lambda { `#{File.join(@installdir["cygwin"], "bin\\bash.exe")} -login -c "cd #{@installdir['physiome-build']} && rm -rf physiome-build && hg clone http://bitbucket.org/a1kmm/physiome-build/ physiome-build"`
                                     msvc9_config
                                     para "Physiome build scripts installed"  },
    'cppunit'            => lambda { # First uncompress cppunit
                                     FileUtils.mkdir_p "#{@installdir['cppunit']}"
                                     cppunitloci = `#{File.join(@installdir['cygwin'], 'bin\\bash.exe')} -login -c 'cygpath --unix "#{@installdir['cppunit']}"'`
                                     cppunitlocf = cppunitloci + "/" + @localpackage['cppunit']
                                     cppunitlocp = `#{File.join(@installdir['cygwin'], 'bin\\bash.exe')} -login -c 'cygpath --unix "#{File.join(@packagedir['cppunit'], @localpackage['cppunit'])}"'`
                                     debug "CPPUnit install dir " + cppunitloci
                                     debug "CPPUnit destination " + cppunitlocf
                                     debug "CPPUnit package dir " + cppunitlocp
                                     FileUtils.cp File.join(@packagedir['cppunit'], @localpackage['cppunit']), @installdir['cppunit']
                                     para `#{File.join(@installdir['cygwin'], 'bin\\bash.exe')} -login -c 'pwd && cd "#{cppunitloci}" && pwd && tar -xzf "#{@localpackage['cppunit']}" && mv -r ./cppunit-1.12.1/* ./* && pwd '`
                                     # Run msdev on the included project, building release and debug
                                     # Assume we have  etc on the PATH
                                     #`#{File.join(@installdir["msvc9"], "").to_s} `
                                     # I have to check what the executable for MSVC9 Pro is
                                     #`VCExpress #{File.join(@installdir["cppunit"],'cppunit-1.12.1\src\CppUnitLibraries.dsw')}`
                                     #`cd #{@installdir['cppunit']} && msdev ` 
                                     # && copy lib/cppunit*.lib '"
                                     para "CPPUnit installed\n" },
    'cellml-api-source'  => lambda { para run_cmd_path "#{File.join(@installdir['cygwin'], 'bin\\bash.exe')} -login -c 'cd #{@installdir['cellml-api-source']} && hg clone http://cellml-api.hg.sourceforge.net:8000/hgroot/cellml-api/cellml-api'" },
    'opencell-source'  => lambda { para run_cmd_path "#{File.join(@installdir['cygwin'], 'bin\\bash.exe')} -login -c 'cd #{@installdir['opencell-source']} && hg clone http://cellml-opencell.hg.sourceforge.net:8000/hgroot/cellml-opencell/cellml-opencell'" }
  }
  @postinstallhook = {
    #'apt-cyg'           => -> { `bash.exe /c "apt-cyg install mercurial zip tar python ed patch flex bison lapack subversion" ` }
  }
  @pages = []
  #makepage @pages[0]
  @pages = [
    lambda {
      projectpage
    },
    lambda {
      # set up list of packages to install
      selected_projects = @projects.map { |name, c| name if c.checked? }.compact
      selected_packages = selected_projects.map { |proj| @project2package[proj] }
      selected_packages.flatten!
      selected_packages.uniq!
      # build a linear order out of dependancies
      @order = []
      @order = walk_dependancies(selected_packages, @dependancies, @order)        
      # set download location, whether to download
      @downloadlist = []
    #},
    #lambda {
      #@listloc.append stack do
        para "Chose download location, and whether to download"
        @order.each do |thing|
          unless @url[thing] == nil
            flow { @q = check :checked => true ; para thing; @r = edit_line @packagedir[thing] ; @s = edit_line @localpackage[thing] }
            @downloadlist.push [thing, @q, @r, @s]
          end
        end
    },
    lambda {
        # "Download"
          @to_download = @downloadlist.map { |name, c, d, e| [name, d.text, e.text] if c.checked? }.compact
          # set install location, whether to install
          # download all that need downloading
          debug "Downloading stuff now"
          debug @order.join(", ")
          @total_downloads = @to_download.length
          debug "Total to download " + @total_downloads.to_s
          @total_downloaded = 0
          @to_download.each do |item, itemloc, itemname|
            debug item.to_s
            unless @url[item] == nil
              #Set real download location
              @packagedir[item] = itemloc
              @localpackage[item] = itemname
              debug "Starting download of " + @url[item].to_s
              unless File.exists?(itemloc)
                FileUtils.mkdir_p(itemloc, {:mode => 0755})
              end
              #@list.append do
                stack do
                  background "#eee".."#ccd"
                  stack :margin => 10 do
                    dl = nil
                    para item, " [", link("cancel") { dl.abort }, "]", :margin => 0
                    d = inscription "Beginning transfer.", :margin => 0
                    p = progress :width => 1.0, :height => 14
                    dl = download @url[item], :save => File.join(itemloc, itemname),
                      :progress => proc { |dl| 
                        d.text = "Transferred #{dl.transferred} of #{dl.length} bytes (#{dl.percent}%)"
                        p.fraction = dl.percent * 0.01 
                        @nextbutton.hide },
                      :finish => proc { |dl|
                        d.text = "Download completed"
                        @total_downloaded += 1
                        debug "Another one downloaded; now we have " + @total_downloaded.to_s
                        if @total_downloaded == @total_downloads
                          @nextbutton.show
                        else
                          @nextbutton.hide
                        end  }
                  end
                end
              #end
            end
          end
          #@list.append do
          #      @nextbutton = button "Install downloaded components", :hidden => true do
        },
        lambda {
                  
                    para "Select list of local packages to install, and the install directories"
                    @install_list = []
                    @order.each do |thing|
                      flow { @q = check :checked => true ; para thing; @r = edit_line @installdir[thing] }
                      @install_list.push [thing, @q, @r]
                    end
         },
         lambda {
                    #@install_button = button "Install packages" do
                      para "Installing..."
                      @to_install = @install_list.map { |name, c, d| [name, d.text] if c.checked? }.compact

                      @to_install.each do |item, itemloc|
                        @installdir[item] = itemloc
                        @installhook[item].call unless @installhook[item] == nil
                      end
          #end
        }

      # run hooks for each that need hooks
    ]
  @pagesfinal = [
    Installerpage.new(@pages[0], [["Select packages to download", 1]]),
    #Installerpage.new(@pages[1], [["Select projects", 0], ["Select download loacation", 2]]),
    Installerpage.new(@pages[1], [["Select packages to download", 0], ["Download packages", 2]]),
    Installerpage.new(@pages[2], [["Select packages to install", 3]]),
    Installerpage.new(@pages[3], [["Install packages", 4]]),
    Installerpage.new(@pages[4], [["Install another project", 0]])
  ]
  makepage @pagesfinal[0]
end
