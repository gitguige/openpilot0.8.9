#!/usr/bin/env python3
import argparse
import carla # pylint: disable=import-error
import math
import numpy as np
import time
import threading
from cereal import log
from multiprocessing import Process, Queue
from typing import Any

import cereal.messaging as messaging
from common.params import Params
from common.numpy_fast import clip
from common.realtime import Ratekeeper, DT_DMON
from lib.can import can_function
from selfdrive.car.honda.values import CruiseButtons
from selfdrive.test.helpers import set_params_enabled

import sys

parser = argparse.ArgumentParser(description='Bridge between CARLA and openpilot.')
parser.add_argument('--joystick', action='store_true')
parser.add_argument('--low_quality', action='store_true')
parser.add_argument('--town', type=str, default='Town04_Opt')
parser.add_argument('--spawn_point', dest='num_selected_spawn_point',
        type=int, default=16)

args = parser.parse_args()

W, H = 1164, 874
REPEAT_COUNTER = 5
PRINT_DECIMATION = 100
STEER_RATIO = 15.

pm = messaging.PubMaster(['roadCameraState', 'sensorEvents', 'can', "gpsLocationExternal"])
sm = messaging.SubMaster(['carControl','controlsState','radarState'])

class VehicleState:
  def __init__(self):
    self.speed = 0
    self.angle = 0
    self.bearing_deg = 0.0
    self.vel = carla.Vector3D()
    self.cruise_button= 0
    self.is_engaged=False

def steer_rate_limit(old, new):
  # Rate limiting to 0.5 degrees per step
  limit = 0.5
  if new > old + limit:
    return old + limit
  elif new < old - limit:
    return old - limit
  else:
    return new

frame_id = 0
def cam_callback(image):
  global frame_id
  img = np.frombuffer(image.raw_data, dtype=np.dtype("uint8"))
  img = np.reshape(img, (H, W, 4))
  img = img[:, :, [0, 1, 2]].copy()

  dat = messaging.new_message('roadCameraState')
  dat.roadCameraState = {
    "frameId": image.frame,
    "image": img.tobytes(),
    "transform": [1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0]
  }
  pm.send('roadCameraState', dat)
  frame_id += 1

def imu_callback(imu, vehicle_state):
  vehicle_state.bearing_deg = math.degrees(imu.compass)
  dat = messaging.new_message('sensorEvents', 2)
  dat.sensorEvents[0].sensor = 4
  dat.sensorEvents[0].type = 0x10
  dat.sensorEvents[0].init('acceleration')
  dat.sensorEvents[0].acceleration.v = [imu.accelerometer.x, imu.accelerometer.y, imu.accelerometer.z]
  # copied these numbers from locationd
  dat.sensorEvents[1].sensor = 5
  dat.sensorEvents[1].type = 0x10
  dat.sensorEvents[1].init('gyroUncalibrated')
  dat.sensorEvents[1].gyroUncalibrated.v = [imu.gyroscope.x, imu.gyroscope.y, imu.gyroscope.z]
  pm.send('sensorEvents', dat)

def panda_state_function(exit_event: threading.Event):
  pm = messaging.PubMaster(['pandaState'])
  while not exit_event.is_set():
    dat = messaging.new_message('pandaState')
    dat.valid = True
    dat.pandaState = {
      'ignitionLine': True,
      'pandaType': "blackPanda",
      'controlsAllowed': True,
      'safetyModel': 'hondaNidec'
    }
    pm.send('pandaState', dat)
    time.sleep(0.5)

def gps_callback(gps, vehicle_state):
  dat = messaging.new_message('gpsLocationExternal')

  # transform vel from carla to NED
  # north is -Y in CARLA
  velNED = [
    -vehicle_state.vel.y, # north/south component of NED is negative when moving south
    vehicle_state.vel.x, # positive when moving east, which is x in carla
    vehicle_state.vel.z,
  ]

  dat.gpsLocationExternal = {
    "timestamp": int(time.time() * 1000),
    "flags": 1, # valid fix
    "accuracy": 1.0,
    "verticalAccuracy": 1.0,
    "speedAccuracy": 0.1,
    "bearingAccuracyDeg": 0.1,
    "vNED": velNED,
    "bearingDeg": vehicle_state.bearing_deg,
    "latitude": gps.latitude,
    "longitude": gps.longitude,
    "altitude": gps.altitude,
    "speed": vehicle_state.speed,
    "source": log.GpsLocationData.SensorSource.ublox,
  }

  pm.send('gpsLocationExternal', dat)

# Create a radar's callback that just prints the data 
# def radar_callback(weak_radar, sensor_data):
def radar_callback( sensor_data):
  # self = weak_radar()
  # if not self:
  #   return
  # print("==============",len(sensor_data),'==============')
  # for detection in sensor_data:
  #   print('depth: ' + str(detection.depth)) # meters 
  #   print('azimuth: ' + str(detection.azimuth)) # rad 
  #   print('altitude: ' + str(detection.altitude)) # rad 
  #   print('velocity: ' + str(detection.velocity)) # m/s

  ret = 0#sensor_data[0]



def fake_driver_monitoring(exit_event: threading.Event):
  pm = messaging.PubMaster(['driverState','driverMonitoringState'])
  while not exit_event.is_set():
    # dmonitoringmodeld output
    dat = messaging.new_message('driverState')
    dat.driverState.faceProb = 1.0
    pm.send('driverState', dat)

    # dmonitoringd output
    dat = messaging.new_message('driverMonitoringState')
    dat.driverMonitoringState = {
      "faceDetected": True,
      "isDistracted": False,
      "awarenessStatus": 1.,
    }
    pm.send('driverMonitoringState', dat)

    time.sleep(DT_DMON)

def can_function_runner(vs: VehicleState, exit_event: threading.Event):
  i = 0
  while not exit_event.is_set():
    can_function(pm, vs.speed, vs.angle, i, vs.cruise_button, vs.is_engaged)
    time.sleep(0.01)
    i+=1


def bridge(q):

  # setup CARLA
  client = carla.Client("127.0.0.1", 2000)
  client.set_timeout(10.0)
  world = client.load_world(args.town)
  
  print("test======================================================================")
  print(args.town)

  if args.low_quality:
    world.unload_map_layer(carla.MapLayer.Foliage)
    world.unload_map_layer(carla.MapLayer.Buildings)
    world.unload_map_layer(carla.MapLayer.ParkedVehicles)
    world.unload_map_layer(carla.MapLayer.Particles)
    world.unload_map_layer(carla.MapLayer.Props)
    world.unload_map_layer(carla.MapLayer.StreetLights)

  blueprint_library = world.get_blueprint_library()

  world_map = world.get_map()

  vehicle_bp = blueprint_library.filter('vehicle.tesla.*')[1]
  spawn_points = world_map.get_spawn_points()
  assert len(spawn_points) > args.num_selected_spawn_point, \
    f'''No spawn point {args.num_selected_spawn_point}, try a value between 0 and
    {len(spawn_points)} for this town.'''
  spawn_point = spawn_points[args.num_selected_spawn_point] # y -= 100+
  spawn_point.location.y   -= 80

  vehicle = world.spawn_actor(vehicle_bp, spawn_point)

  #=====add second vehicle=====
  spawn_point2 = spawn_point
  spawn_point2.location.y   += 100#20

  vehicle2 = world.spawn_actor(vehicle_bp, spawn_point2)
  # vehicle2.set_autopilot(True)

  spectator = world.get_spectator()
  transform = vehicle.get_transform()
  spectator.set_transform(carla.Transform(transform.location + carla.Location(z=150), carla.Rotation(pitch=-90)))

  #======end line===============

  max_steer_angle = vehicle.get_physics_control().wheels[0].max_steer_angle

  # make tires less slippery
  # wheel_control = carla.WheelPhysicsControl(tire_friction=5)
  physics_control = vehicle.get_physics_control()
  physics_control.mass = 2326
  # physics_control.wheels = [wheel_control]*4
  physics_control.torque_curve = [[20.0, 500.0], [5000.0, 500.0]]
  physics_control.gear_switch_time = 0.0
  vehicle.apply_physics_control(physics_control)

  blueprint = blueprint_library.find('sensor.camera.rgb')
  blueprint.set_attribute('image_size_x', str(W))
  blueprint.set_attribute('image_size_y', str(H))
  blueprint.set_attribute('fov', '70')
  blueprint.set_attribute('sensor_tick', '0.05')
  transform = carla.Transform(carla.Location(x=0.8, z=1.13))
  camera = world.spawn_actor(blueprint, transform, attach_to=vehicle)
  camera.listen(cam_callback)

  vehicle_state = VehicleState()

  # reenable IMU
  imu_bp = blueprint_library.find('sensor.other.imu')
  imu = world.spawn_actor(imu_bp, transform, attach_to=vehicle)
  imu.listen(lambda imu: imu_callback(imu, vehicle_state))

  gps_bp = blueprint_library.find('sensor.other.gnss')
  gps = world.spawn_actor(gps_bp, transform, attach_to=vehicle)
  gps.listen(lambda gps: gps_callback(gps, vehicle_state))

  
  # # Get radar blueprint 
  # radar_bp = blueprint_library.filter('sensor.other.radar')[0]

  # # Set Radar attributes, by default are: 
  # radar_bp.set_attribute('horizontal_fov', '30') # degrees 
  # radar_bp.set_attribute('vertical_fov', '30') # degrees 
  # radar_bp.set_attribute('points_per_second', '1500')
  # radar_bp.set_attribute('range', '100') # meters 

  # # Spawn the radar 
  # radar = world.spawn_actor(radar_bp, transform, attach_to=vehicle)
  # # weak_radar = weakref.ref(radar)
  # # radar.listen(lambda sensor_data: radar_callback(weak_radar, sensor_data))
  # radar.listen(radar_callback)



  # launch fake car threads
  threads = []
  exit_event = threading.Event()
  threads.append(threading.Thread(target=panda_state_function, args=(exit_event,)))
  threads.append(threading.Thread(target=fake_driver_monitoring, args=(exit_event,)))
  threads.append(threading.Thread(target=can_function_runner, args=(vehicle_state, exit_event,)))
  for t in threads:
    t.start()

  # can loop
  rk = Ratekeeper(100, print_delay_threshold=0.05) #rate =100, T=1/100s=10ms

  # init
  throttle_ease_out_counter = REPEAT_COUNTER
  brake_ease_out_counter = REPEAT_COUNTER
  steer_ease_out_counter = REPEAT_COUNTER


  vc = carla.VehicleControl(throttle=0, steer=0, brake=0, reverse=False)

  is_openpilot_engaged = False
  throttle_out = steer_out = brake_out = 0
  throttle_op = steer_op = brake_op = 0
  throttle_manual = steer_manual = brake_manual = 0

  old_steer = old_brake = old_throttle = 0
  throttle_manual_multiplier = 0.7 #keyboard signal is always 1
  brake_manual_multiplier = 0.7 #keyboard signal is always 1
  steer_manual_multiplier = 45 * STEER_RATIO  #keyboard signal is always 1

  tm = client.get_trafficmanager(8008)
  # vehicle2.set_autopilot(True,8008)
  tm.vehicle_percentage_speed_difference(vehicle2,-20) #Sets the difference the vehicle's intended speed and its current speed limit.
  # tm.distance_to_leading_vehicle(vehicle2,5)
  # cruise_button = CruiseButtons.RES_ACCEL
  # is_openpilot_engaged = True
  # q.put("cruise_up")

  frame_ID = 0
  FI_flage = 0
  speed = 0
  FI_time_budget = 250 #250*10ms =2.5s
  while 1:
    if is_openpilot_engaged:
      frame_ID += 1
    # if frame_ID >2000:
    #   q.put("quit")
    # 1. Read the throttle, steer and brake from op or manual controls
    # 2. Set instructions in Carla
    # 3. Send current carstate to op via can

    cruise_button = 0
    throttle_out = steer_out = brake_out = 0.0
    throttle_op = steer_op = brake_op = 0
    throttle_manual = steer_manual = brake_manual = 0.0

    # --------------Step 1-------------------------------
    if not q.empty():
      message = q.get()
      m = message.split('_')
      print(message)
      if m[0] == "steer":
        steer_manual = float(m[1])
        is_openpilot_engaged = False
      elif m[0] == "throttle":
        throttle_manual = float(m[1])
        is_openpilot_engaged = False
      elif m[0] == "brake":
        brake_manual = float(m[1])
        is_openpilot_engaged = False
      elif m[0] == "reverse":
        #in_reverse = not in_reverse
        cruise_button = CruiseButtons.CANCEL
        is_openpilot_engaged = False
      elif m[0] == "cruise":
        vehicle2.set_autopilot(True,8008)
        if m[1] == "down":
          cruise_button = CruiseButtons.DECEL_SET
          is_openpilot_engaged = True
        elif m[1] == "up":
          cruise_button = CruiseButtons.RES_ACCEL
          is_openpilot_engaged = True
        elif m[1] == "cancel":
          cruise_button = CruiseButtons.CANCEL
          is_openpilot_engaged = False
      elif m[0] == "a":
        FI_flage = 1 -FI_flage 
      elif m[0] == "quit":
        vehicle2.set_autopilot(False,8008)
        break

      throttle_out = throttle_manual * throttle_manual_multiplier
      steer_out = steer_manual * steer_manual_multiplier
      brake_out = brake_manual * brake_manual_multiplier

      #steer_out = steer_out
      # steer_out = steer_rate_limit(old_steer, steer_out)
      old_steer = steer_out
      old_throttle = throttle_out
      old_brake = brake_out

    dRel = 0
    yRel = 2.5
    vRel = 0
    vLead = 0

      # print('message',old_throttle, old_steer, old_brake)

    if is_openpilot_engaged:
      sm.update(0)
      # TODO gas and brake is deprecated
      throttle_op = clip(sm['carControl'].actuators.accel/4.0, 0.0, 1.0)
      brake_op = clip(-sm['carControl'].actuators.accel/4.0, 0.0, 1.0)
      steer_op = sm['carControl'].actuators.steeringAngleDeg

      throttle_out = throttle_op
      steer_out = steer_op
      brake_out = brake_op

      steer_out = steer_rate_limit(old_steer, steer_out)
      old_steer = steer_out

      dRel = sm['radarState'].leadOne.dRel
      yRel = sm['radarState'].leadOne.yRel
      vRel = sm['radarState'].leadOne.vRel
      vLead = sm['radarState'].leadOne.vLead

    else:
      if throttle_out==0 and old_throttle>0:
        if throttle_ease_out_counter>0:
          throttle_out = old_throttle
          throttle_ease_out_counter += -1
        else:
          throttle_ease_out_counter = REPEAT_COUNTER
          old_throttle = 0

      if brake_out==0 and old_brake>0:
        if brake_ease_out_counter>0:
          brake_out = old_brake
          brake_ease_out_counter += -1
        else:
          brake_ease_out_counter = REPEAT_COUNTER
          old_brake = 0

      if steer_out==0 and old_steer!=0:
        if steer_ease_out_counter>0:
          steer_out = old_steer
          steer_ease_out_counter += -1
        else:
          steer_ease_out_counter = REPEAT_COUNTER
          old_steer = 0

    # --------------Step 2-------------------------------

    steer_carla = steer_out / (max_steer_angle * STEER_RATIO * -1)

    steer_carla = np.clip(steer_carla, -1,1)
    steer_out = steer_carla * (max_steer_angle * STEER_RATIO * -1)
    old_steer = steer_carla * (max_steer_angle * STEER_RATIO * -1)


    # #FI random
    # if frame_ID>3000 and  frame_ID<10000:#FI_flage:
    #   if FI_flage ==0:
    #     print("===============start fault injection!==========")
    #     FI_flage =1
    #   throttle_out +=0.5
    #   if throttle_out >1:
    #     throttle_out = 0.99
    #   brake_out = 0
    # elif FI_flage:
    #   FI_flage = 0
    # #==============

    #FI CAWT
    if FI_flage ==0:
      if speed !=0:
        if vRel<0 and dRel/speed <2:#FI_flage:
          print("===============start fault injection!==========")
          FI_flage =1
       

    if FI_flage:
      throttle_out =1.2
      brake_out = 0      
      FI_time_budget -= 1
      if FI_time_budget <=0:
        FI_flage = 0
        print("===============Stop fault injection!==========")
    #==============
    
    vc.throttle = throttle_out/0.6
    vc.steer = steer_carla
    vc.brake = brake_out
    vehicle.apply_control(vc)

    # vehicle2.apply_control(vc)

    # measurements, sensor_data = client.read_data()
    # control = measurements.player_measurements.autopilot_control
    # client.send_control(control)

    # --------------Step 3-------------------------------
    vel = vehicle.get_velocity()
    speed = math.sqrt(vel.x**2 + vel.y**2 + vel.z**2) # in m/s
    vehicle_state.speed = speed
    vehicle_state.vel = vel
    vehicle_state.angle = steer_out
    vehicle_state.cruise_button = cruise_button
    vehicle_state.is_engaged = is_openpilot_engaged

    # if rk.frame%PRINT_DECIMATION == 0:
    if rk.frame%PRINT_DECIMATION == 0 or dRel<1 and dRel != 0:
      print("Frame ID:",frame_ID,"frame: ", "engaged:", is_openpilot_engaged, "; throttle: ", round(vc.throttle, 3), "; steer(c/deg): ", round(vc.steer, 3), round(steer_out, 3), "; brake: ", round(vc.brake, 3),\
            "speed:",round(speed,2),'vLead:',round(vLead,2),"vRel",round(vRel,2),"drel:",round(dRel,2),round(yRel,2))

    rk.keep_time()
    # print(rk.frame)

    if dRel <0:
      break

  # Clean up resources in the opposite order they were created.
  exit_event.set()
  for t in reversed(threads):
    t.join()
    # t.stop()
  gps.destroy()
  imu.destroy()
  camera.destroy()
  vehicle.destroy()

  vehicle2.set_autopilot(False,8008)
  vehicle2.destroy()
  sys.exit(0)
  # exit()


def bridge_keep_alive(q: Any):
  while 1:
    try:
      bridge(q)
      break
    except RuntimeError:
      print("Restarting bridge...")

if __name__ == "__main__":
  # make sure params are in a good state
  set_params_enabled()

  msg = messaging.new_message('liveCalibration')
  msg.liveCalibration.validBlocks = 20
  msg.liveCalibration.rpyCalib = [0.0, 0.0, 0.0]
  Params().put("CalibrationParams", msg.to_bytes())

  q: Any = Queue()
  p = Process(target=bridge_keep_alive, args=(q,), daemon=True)
  p.start()

  if 0:#args.joystick:
    # start input poll for joystick
    from lib.manual_ctrl import wheel_poll_thread
    wheel_poll_thread(q)
    p.join()
  else:
    # start input poll for keyboard
    from lib.keyboard_ctrl import keyboard_poll_thread
    keyboard_poll_thread(q)
