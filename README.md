# openpilot0.8.9
This is an experiment platform with autonomous agent openpilot0.8.9 and simulator carla 9.11 without docker setups.

## steps to setup the environment
1. clone the code from this repository
```
git clone https://github.com/gitguige/openpilot0.8.9.git
cd openpilot0.8.9
```

2. extract phonelibs.zip to replace ./phonelibs/

3. activate the virtual environment 

4. scons -c && scons -j$(nproc)


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
./run_brisge.sh (cruise_speed_lead) (initial_relative_distance) (new cruise_speed_lead)
```

## steps to run simualations with fault injection
replace the last step above with the following instruction:
```
./run_fault_inject_XXX.sh (e.g., run_fault_inject_monitor_V2_campaign.sh for random FI)
```