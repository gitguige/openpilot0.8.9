#!/usr/bin/env python3

import carla

# from agents.navigation.behavior_agent import BehaviorAgent  # pylint: disable=import-error
# from agents.navigation.roaming_agent import RoamingAgent  # pylint: disable=import-error
# from agents.navigation.basic_agent import BasicAgent  # pylint: disable=import-error

client = carla.Client("127.0.0.1", 2000)
client.set_timeout(10.0)
# world = client.get_world()
world = client.load_world("Town04_Opt")


blueprint_library = world.get_blueprint_library()
world_map = world.get_map()
vehicle_bp = blueprint_library.filter('vehicle.tesla.*')[1]

# transform = carla.Transform()
# transform.location = carla.Location(100.0, 0.0, 0.0)

spawn_points = world_map.get_spawn_points()

# spawn_point = spawn_points[args.num_selected_spawn_point]
# vehicle = world.spawn_actor(vehicle_bp, transform.location )

spawn_point = spawn_points[16]
vehicle = world.spawn_actor(vehicle_bp, spawn_point)

spawn_point.location.y   += 10
vehicle2 = world.spawn_actor(vehicle_bp, spawn_point)


spectator = world.get_spectator()
transform = vehicle.get_transform()
spectator.set_transform(carla.Transform(transform.location + carla.Location(z=100), carla.Rotation(pitch=-90)))

vehicle.set_autopilot(True)
vehicle2.set_autopilot(True)




vehicle.destroy()
vehicle2.destroy()