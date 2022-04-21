# openpilot0.8.9
This is an experiment platform with autonomous agent openpilot0.8.9 and simulator carla 9.11 with or without docker setups.

## Recommended system
* Ubuntu 20.04
* NVIDIA RTX 2080, RTX 3070, RTX 3080, RTX 3090 or higher
* Python 3.8.10

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

3. Insatall CARLA simulator following the instructions [here](http://carla.readthedocs.io/en/0.9.11/start_quickstart/)

## steps to setup the openpilot environment
1. clone the code from this repository
```
git clone https://github.com/gitguige/openpilot0.8.9.git
cd openpilot0.8.9
```

2. extract phonelibs.zip to replace ./phonelibs/

3. install dependencies to run the simulation without docker using the autoscript (skip this step with docker setups)

```
sudo chmod +x setup_autoscript.sh

./setup_autoscript.sh
```

A manual instruction to install the dependencies is also included in *README_install_op-denpendency.md* 

4. activate the virtual environment 

5. scons -c && scons -j$(nproc)


## steps to run the simulation with CARLA
1. run carla 9.11 simulator
```
./start_carla.sh #(with docker)
```

2. open a new terminal and run openpilot threads
```
cd tools/sim/ 
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
