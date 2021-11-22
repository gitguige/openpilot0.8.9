# openpilot0.8.9
This is an experiment platform with autonomous agent openpilot0.8.9 and simulator carla 9.11 without docker setups.

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
./run_brisge.sh (cruise_speed_lead) (initial_relative_distance)
```

## steps to run simualations with fault injection
replace the last step above with the following instruction:
```
./run_fault_inject_XXX.sh
```