# -*- mode: ruby -*-
# vi: set ft=ruby :

# Vagrantfile API/syntax version. Don't touch unless you know what you're doing!
VAGRANTFILE_API_VERSION = "2"

Vagrant.configure(VAGRANTFILE_API_VERSION) do |config|
  # All Vagrant configuration is done here. The most common configuration
  # options are documented and commented below. For a complete reference,
  # please see the online documentation at vagrantup.com.

  # Every Vagrant virtual environment requires a box to build off of.
  config.vm.box = "ubuntu/trusty64"
  config.vm.network "public_network"

  config.vm.provider "virtualbox" do |vb|  
    # Use VBoxManage to customize the VM. For example to change memory:
    vb.customize ["modifyvm", :id, "--memory", "2048"]
    vb.customize ["modifyvm", :id, "--cpus", "2"]
    vb.customize ["modifyvm", :id, "--natdnshostresolver1", "on"]
    vb.customize ["modifyvm", :id, "--natdnsproxy1", "on"]
  end
   
  # Mount the data and tiles folder.  Setup for Jason's machine.
  config.vm.synced_folder "d:/geodata", "/data"
  config.vm.synced_folder "d:/tiles", "/tiles"
   
  #config.vm.synced_folder "readymap", "/var/www/readymap/readymap", create: true, owner: "vagrant", group: "vagrant"
  #config.vm.synced_folder "D:/geodata", "/data"
  #config.vm.synced_folder "D:/tiles", "/tiles"
  #config.vm.synced_folder "D:/dev/geochain", "/geochain"
   
  #config.vm.synced_folder "readymap", "/var/www/readymap/readymap",      
  #    create: true,
  #    owner: "vagrant",
  #    group: "vagrant",
  #    type: "rsync",
  #    rsync__args: ["--verbose", "--archive", "-z", "--chmod=ug=rwX,o=rxX"],
  #    rsync__exclude: ".git/"

  #config.vm.provision "shell", path: "vagrant_install.sh"
end
 
