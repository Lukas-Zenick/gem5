#curl -L http://cdimage.ubuntu.com/ubuntu-base/releases/20.04/release/ubuntu-base-20.04.1-base-amd64.tar.gz -o ubuntu-base-20.04.1.tar.gz
util/gem5img.py init ubuntu-x86.img 8192
util/gem5img.py mount ubuntu-x86.img ../mnt
sudo tar -xvzf ubuntu.tar.gz -C ../mnt
sudo cp -r test-source ../mnt/.
sudo chroot ../mnt /bin/bash << EOT
echo "kernel.randomize_va_space = 0" > /etc/sysctl.d/01-disable-aslr.conf
cd /test-source
make
EOT
util/gem5img.py umount ../mnt
