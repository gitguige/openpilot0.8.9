1. install virtualenv

2. setup a virtual environment of python 3.8.10 (If it says pip not working, please go to step 8 and see the note)

3. activate the virtual environment

4. ```pip install numpy matplotlib scipy```

5. 
```
sudo apt-get update && sudo apt-get install -y --no-install-recommends autoconf build-essential bzip2 ca-certificates capnproto clang cmake cppcheck curl ffmpeg gcc-arm-none-eabi git iputils-ping libarchive-dev libbz2-dev libcapnp-dev libcurl4-openssl-dev libeigen3-dev libffi-dev libgles2-mesa-dev libglew-dev libglib2.0-0 liblzma-dev libomp-dev libopencv-dev libqt5sql5-sqlite libqt5svg5-dev libsqlite3-dev libssl-dev libsystemd-dev libusb-1.0-0-dev libzmq3-dev locales ocl-icd-libopencl1 ocl-icd-opencl-dev opencl-headers python-dev qml-module-qtquick2 qt5-default qtlocation5-dev qtmultimedia5-dev qtpositioning5-dev qtwebengine5-dev sudo valgrind wget 
```


6. ```sudo rm -rf /var/lib/apt/lists/*```

7. ```pip install --no-cache-dir pipenv==2020.8.13 && pipenv install --system --deploy --dev --clear && pip uninstall -y pipenv ```(run this inside openpilot/) (pygame 2.0.0.dev8 no longer exists. Please manually install pygame 2.0.0 instead

8. 
```
sudo apt-get update && sudo apt-get install -y --no-install-recommends apt-utils unzip tar curl xz-utils alien dbus gcc-arm-none-eabi tmux vim lsb-core libx11-6
```

Note: If there is a dependency issue while installing vim, try the solution in these [links1](https://superuser.com/questions/1629186/i-am-unable-to-install-vim-on-my-machine-unmet-dependency-libpython3-8)
[link2](https://stackoverflow.com/questions/61627422/upgrade-ubuntu-18-04-to-20-04-but-packages-remain-bionic1/67260221#67260221)

Please remember to do an “apt-cache showpkg python3.8” and change the dependencies’ versions to 3.8.10 according to the output of apt-cache (e.g. 3.8.10-0ubuntu1~20.04.1) (This issue usually occurs if the machine has been upgraded from ubuntu 18 to 20)

9. ```sudo rm -rf /var/lib/apt/lists/* ```

10. ```sudo apt-get update && sudo apt-get install --no-install-recommends make build-essential libssl-dev zlib1g-dev libbz2-dev libreadline-dev libsqlite3-dev wget curl llvm libncurses5-dev xz-utils tk-dev libxml2-dev libxmlsec1-dev libffi-dev liblzma-dev```

11. complie the code

12. Skip this step if you don't have any error with last step.

Install other dependencies specified in each Dockerfile under /opendbc; /panda; /tools/sim; /cereal; /rednose_repo; (please remember to install pip packages inside all the requirements.txt files you can find under these directories)
