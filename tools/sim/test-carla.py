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
spawn_point.location.y   -= 80

#=====add 1st vehicle=====
spawn_point1 = carla.Transform(spawn_point.location,spawn_point.rotation)
# spawn_point1.location.y   += 20
vehicle = world.spawn_actor(vehicle_bp, spawn_point1)

#=====add second vehicle=====
spawn_point2 = carla.Transform(spawn_point.location,spawn_point.rotation)
spawn_point2.location.y   += 30#20
vehicle2 = world.spawn_actor(vehicle_bp, spawn_point2)
# vehicle2.set_autopilot(True)

#==========3rd vehilce===========
spawn_point3 = carla.Transform(spawn_point.location,spawn_point.rotation)
spawn_point3.location.y   -= 35
spawn_point3.location.x   += 7
spawn_point3.rotation.yaw += 25
vehicle3 = world.spawn_actor(vehicle_bp, spawn_point3)

#=====add 4-5 vehicle=====
spawn_point4 = carla.Transform(spawn_point1.location,spawn_point1.rotation)
spawn_point4.location.x   += 4
spawn_point4.location.y   += 15
vehicle4 = world.spawn_actor(vehicle_bp, spawn_point4)

spawn_point5 = carla.Transform(spawn_point1.location,spawn_point1.rotation)
spawn_point5.location.x   += 5
spawn_point5.location.y   -= 15
spawn_point5.rotation.yaw += 13
vehicle5 = world.spawn_actor(vehicle_bp, spawn_point5)



spectator = world.get_spectator()
transform = vehicle.get_transform()
spectator.set_transform(carla.Transform(transform.location + carla.Location(z=100), carla.Rotation(pitch=-90)))

vehicle.set_autopilot(True)
vehicle2.set_autopilot(True)




vehicle.destroy()
vehicle2.destroy()
vehicle3.destroy()