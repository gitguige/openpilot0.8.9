# openpilot0.8.9
This is an experiment platform with autonomous agent openpilot0.8.9 and simulator carla 9.11 with or without docker setups.

Link to Perception Attack Code: https://github.com/gitguige/CAP-Attack


HOW To CITE:

[1] X. Zhou, A. Schmedding, H. Ren, L. Yang, P. Schowitz, E. Smirni, H. Alemzadeh, “Strategic Safety-Critical Attacks against an Advanced Driver Assistance System,” in the 52nd IEEE/IFIP International Conference on Dependable Systems and Networks (DSN 2022), 2022.

[2] X. Zhou, A. Chen, Ma. Kouzel, H. Ren, M. McCarty, C. Nita-Rotaru, and H. Alemzadeh, "Runtime Stealthy Perception Attacks against DNN-based Adaptive Cruise Control Systems," in ACM Asia Conference on Computer and Communications Security (ASIA CCS ’25), 2025.


## Recommended system
* Ubuntu 20.04
* NVIDIA RTX 2080, RTX 3070, RTX 3080, RTX 3090 or higher
* Python 3.8.10
* pip >= 20.0.2

## steps to setup the environment
1. Check the recommended Nvidia driver and install it.
```
sudo apt-get update
sudo apt-get upgrade -y
ubuntu-drivers devices
```

2. Insatll Docker if you want to run the simulation in docker (optional).
```
sudo apt install curl

curl https://get.docker.com | sh \
&& sudo systemctl start docker \
&& sudo systemctl enable docker
```

## steps to setup the openpilot environment
1. clone the code from this repository
```
git clone https://github.com/gitguige/openpilot0.8.9.git
cd openpilot0.8.9
```
**Note:** if your files under openpilot0.8.9/models are very small (<5MB), you may need to manually download them again from the repository or install *Git LFS* to clone te repo again.


2. extract phonelibs.zip to replace ./phonelibs/

3. make a virtual environment and activate it
```
sudo apt-get install virtualenv
virtualenv --python=/usr/bin/python3.8 ~/venvOPnew
source ~/venvOPnew/bin/activate
```

4. install dependencies to run the simulation without docker using the autoscript (skip this step with docker setups)

```
sudo chmod +x setup_autoscript.sh
./setup_autoscript.sh
```
   A manual instruction to install the dependencies is also included in *README_install_op-denpendency.md* 

5. scons -c && scons -j$(nproc)


## install CARLA
1. Insatall CARLA simulator following the instructions [here](http://carla.readthedocs.io/en/0.9.11/start_quickstart/)

2. install carla lib for docker setups (skip this step if you don't use docker)
```
source ~/venvOPnew/bin/activate
cd CARLA_0.9.11
easy_install PythonAPI/carla/dist/carla-0.9.11-py3.8-linux-x86_64.egg || true
```
If the file *carla-0.9.11-py3.8-linux-x86_64.egg* does not exist, copy one from *carla-0.9.11-py3.x-linux-x86_64.egg* and rename it to *carla-0.9.11-py3.8-linux-x86_64.egg*.

## steps to run the simulation with CARLA
1. run carla 9.11 simulator with docker
```
cd tools/sim/ 
sudo ./start_carla.sh #(with docker)
```
   or without docker: open a terminal under *cd CARLA_0.9.11* and run:
```
./CarlaUE4.sh
```

2. open a new terminal and run openpilot threads
```
./launch_openpilot.sh 
```

3. open a new terminal and run bridge thread
```
./run_bridge.sh (cruise_speed_lead) (initial_relative_distance) (new cruise_speed_lead)
```

## steps to run simualations with fault injection
replace the last step above with the following instruction:
```
./run_fault_inject_XXX.sh (e.g., run_fault_inject_monitor_V2_campaign.sh for random FI)
```
Context-Aware: use STPA FI campaign 1-6;

Random-ST: use random FI campaign 1-6;

Random-DUR: use STPA FI canpaign 11-16;

Radnom-ST-DUR: use random FI campaign 21-26;


## Cite
```
@inproceedings{zhou2022strategic,
  title={Strategic safety-critical attacks against an advanced driver assistance system},
  author={Zhou, Xugui and Schmedding, Anna and Ren, Haotian and Yang, Lishan and Schowitz, Philip and Smirni, Evgenia and Alemzadeh, Homa},
  booktitle={2022 52nd Annual IEEE/IFIP International Conference on Dependable Systems and Networks (DSN)},
  pages={79--87},
  year={2022},
  organization={IEEE}
}

@inproceedings{zhou2025runtime,
  title={Runtime Stealthy Perception Attacks against DNN-based Adaptive Cruise Control Systems},
  author={Zhou, Xugui and Chen, Anqi and Kouzel, Maxfield and Ren, Haotian and McCarty, Morgan and Nita-Rotaru, Cristina and Alemzadeh, Homa},
  booktitle={20th ACM ASIA Conference on Computer and Communications Security (AsiaCCS)},
  year={2025}
}
```
