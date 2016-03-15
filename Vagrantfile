Vagrant.configure('2') do |config|

  # stewie.isi.edu is deb7
  config.vm.box = 'debian/wheezy64'

  # 7.9.2 switched the default syncing mechanism to rsync :-@
  config.vm.box_version = "= 7.9.1"

  config.vm.define 'pegasus-metrics-dev', primary: true do |dev|
    dev.vm.hostname = 'pegasus-metrics-dev'
    dev.vm.network :forwarded_port, :guest => 5000, :host => 5000
    dev.vm.network :forwarded_port, :guest => 80, :host => 5080
  end

  config.vm.provider "virtualbox" do |v|
    v.memory = 1024
  end

  config.vm.provision :shell, :path => 'vagrant_setup.sh'

  config.vm.post_up_message = <<-EOS
    To run the Pegasus metrics server, vagrant ssh, and then:
    $ cd /vagrant
    $ export PEGASUS_METRICS_CONFIG=/vagrant/config.py
    $ python run.py

    This will connect to port 5000 on the VM host.

    You can also use Apache by running:
    $ sudo su -
    $ cd /etc/apache2/sites-enabled
    $ ln -s ../sites-available/pegasus-metrics .
    $ service apache restart

    This will connect to port 5080 on the VM host.
  EOS
end
