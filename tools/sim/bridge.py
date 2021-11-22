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

import sys,os,signal
# from sys import argv


parser = argparse.ArgumentParser(description='Bridge between CARLA and openpilot.')
parser.add_argument('--joystick', action='store_true')
parser.add_argument('--low_quality', action='store_true')
parser.add_argument('--town', type=str, default='Town04_Opt')
parser.add_argument('--spawn_point', dest='num_selected_spawn_point',
        type=int, default=16)

parser.add_argument('--cruise_lead', type=int, default=80) #(1 + 80%)V0 = 1.8V0
parser.add_argument('--init_dist', type=int, default=100) #meters; initial relative distance between vehicle and vehicle2

# parser.add_argument('--faultinfo', type=str, default='')
# parser.add_argument('--scenarioNum', type=int, default=1)
# parser.add_argument('--faultNum', type=int, default=1)


args = parser.parse_args()

W, H = 1164, 874
REPEAT_COUNTER = 5
PRINT_DECIMATION = 100
STEER_RATIO = 15.

vEgo = 40 #mph #set in selfdrive/controlsd
FI_Enable = False#True #False: run the code in fault free mode; True: add fault inejction Engine 

pm = messaging.PubMaster(['roadCameraState', 'sensorEvents', 'can', "gpsLocationExternal"])
sm = messaging.SubMaster(['carControl','controlsState','radarState','modelV2'])

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
  # # self = weak_radar()
  # # if not self:
  # #   return
  # print("==============",len(sensor_data),'==============')
  # for detection in sensor_data:
  #   print(detection)
  #   # print('depth: ' + str(detection.depth)) # meters 
  #   # print('azimuth: ' + str(detection.azimuth)) # rad 
  #   # print('altitude: ' + str(detection.altitude)) # rad 
  #   # print('velocity: ' + str(detection.velocity)) # m/s

  ret = 0#sensor_data[0]

collision_hist = []
def collision_callback(col_event):
  collision_hist.append(col_event)
  # print(col_event)

laneInvasion_hist = []
def laneInvasion_callback(LaneInvasionEvent):
  laneInvasion_hist.append(LaneInvasionEvent)



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

  #=====add second vehicle=====
  spawn_point1 = spawn_point
  # spawn_point1.location.y   += 20
  vehicle = world.spawn_actor(vehicle_bp, spawn_point1)

  #=====add second vehicle=====
  spawn_point2 = spawn_point
  spawn_point2.location.y   += args.init_dist#100#20
  vehicle2 = world.spawn_actor(vehicle_bp, spawn_point2)
  # vehicle2.set_autopilot(True)

  spectator = world.get_spectator()
  transform = vehicle.get_transform()
  spectator.set_transform(carla.Transform(transform.location + carla.Location(z=150), carla.Rotation(pitch=-90)))

  #======end line===============

  max_steer_angle = vehicle.get_physics_control().wheels[0].max_steer_angle
  print('max_steer_angle',max_steer_angle)

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
  # # radar_bp.set_attribute('points_per_second', '1500')
  # radar_bp.set_attribute('range', '100') # meters 

  # # Spawn the radar 
  # radar = world.spawn_actor(radar_bp, transform, attach_to=vehicle, attachment_type=carla.AttachmentType.Rigid)
  # # weak_radar = weakref.ref(radar)
  # # radar.listen(lambda sensor_data: radar_callback(weak_radar, sensor_data))
  # radar.listen(lambda sensor_data: radar_callback(sensor_data))
  # # radar.listen(radar_callback)

  #collision sensor detector
  colsensor_bp = blueprint_library.find("sensor.other.collision")
  colsensor = world.spawn_actor(colsensor_bp, transform, attach_to=vehicle)
  colsensor.listen(lambda colevent: collision_callback(colevent))

  #lane invasion
  laneInvasion_bp = blueprint_library.find("sensor.other.lane_invasion")
  laneInvasion = world.spawn_actor(laneInvasion_bp, transform, attach_to=vehicle)
  laneInvasion.listen(lambda LaneInvasionEvent: laneInvasion_callback(LaneInvasionEvent))



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
  # tm.vehicle_percentage_speed_difference(vehicle2,-(CRUISE_SPEED_LEAD-1)*100) #Sets the difference the vehicle's intended speed and its current speed limit.
  tm.vehicle_percentage_speed_difference(vehicle2,-args.cruise_lead) #Sets the difference the vehicle's intended speed and its current speed limit.
  # tm.distance_to_leading_vehicle(vehicle2,5)
  # cruise_button = CruiseButtons.RES_ACCEL
  # is_openpilot_engaged = True
  # print("is_openpilot_engaged = True~~~~~~~~~~~\n")
  # q.put("cruise_up")
  is_autopilot_engaged =False #vehicle2

  fp_res = open('results/data_ADS1_{}mph_{}m_{}V0.csv'.format(vEgo,args.init_dist,args.cruise_lead),'w')
  fp_res.write("frameIdx,distance(m),speed(m/s),acceleration(m/s2),angle_steer,gas,brake,steer_torque,d_rel(m),v_rel(m/s),c_path(m),faultinjection,alert,hazard,alertMsg,hazardMsg,laneInvasion,yPos,Laneline1,Laneline2,Laneline3,Laneline4,leftPath,rightPath\n")
  speed = 0
  throttle_out_hist = 0
  FI_time_budget = 250 #250*10ms =2.5s
  Num_laneInvasion = 0

  faulttime = -1
  alerttime = -1
  hazardtime = -1
  fault_duration = 0

  hazMsg = ""
  hazard = False

  alertType_list =[]
  alertText1_list = []
  alertText2_list = []

  FI_flage = 0
  frameIdx = 0
  while frameIdx<6000:

    altMsg = ""
    alert = False

    if FI_flage<2: #0/1
      FI_flage = 0
    if is_openpilot_engaged:
      frameIdx += 1

    #simulate button Enable event
    if rk.frame == 750:
      q.put("cruise_up")

    # if frameIdx == 1000:
    #   tm.vehicle_percentage_speed_difference(vehicle2,-100)

    # if frameIdx >2000:
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
    yPos = 0
    ylaneLines = []

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
      yRel = sm['radarState'].leadOne.yRel #y means lateral direction
      vRel = sm['radarState'].leadOne.vRel
      vLead = sm['radarState'].leadOne.vLead
      # if not sm['radarState'].leadOne.status:
      #   dRel = 100

      md = sm['modelV2']
      if len(md.position.y)>0:
        yPos = round(md.position.y[0],2) # position 
        ylaneLines = [round(md.laneLines[0].y[0],2),round(md.laneLines[1].y[0],2),round(md.laneLines[2].y[0],2),round(md.laneLines[3].y[0],2)]
        # print(ylaneLines[2] - yPos)


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

    if speed:
      headway_time = dRel/speed
    else:
      headway_time = 100
    
    RSpeed = -vRel #v_Ego -V_Lead

    if FI_Enable == True:
      # #FI CAWT
      # if FI_flage ==0:
      #   if speed !=0:
      #     if vRel<0 and dRel/speed <2:#FI_flage:
      #       print("===============start fault injection!==========")
      #       FI_flage =1    
      # 
      
      #throttle:HOOK#
      if headway_time<=2.0 and RSpeed>=0 and vLead!=0:
        throttle_out=0.6
        brake_out=0
        FI_flage=1
        
      if FI_flage == 1:
        if faulttime == -1:
          faulttime = frameIdx
        fault_duration += 1
        throttle_out =0.6
        brake_out = 0      
      #   FI_time_budget -= 1
      #   if FI_time_budget <=0:
      #     FI_flage = 2 #quit
      #     print("===============Stop fault injection as the 2.5 s time budget used up!===========")
      # #==============

      # if FI_flage == 2:
      if faulttime >= 0 and frameIdx >250 + faulttime:
        FI_flage = 2
        throttle_out = 0
        brake_out = 1
        steer_carla = 0
    
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
    acc = vehicle.get_acceleration()
    acceleration = math.sqrt(acc.x**2 + acc.y**2 + acc.z**2) # in m/s^2
    if speed==acceleration==0:
      acceleration =1
    vehicle_state.speed = speed
    vehicle_state.vel = vel
    vehicle_state.angle = steer_out
    vehicle_state.cruise_button = cruise_button
    vehicle_state.is_engaged = is_openpilot_engaged

    #controlsState
    alertText1 = sm['controlsState'].alertText1
    alertText2 = sm['controlsState'].alertText2
    alertType  = sm['controlsState'].alertType

    if alertType and alertType not in alertType_list and alertText1 not in alertText1_list:
      alertText1_list.append(alertText1)
      alertType_list.append(alertType)
      if(alerttime== -1 and 'startupMaster/permanent' not in alertType and 'buttonEnable/enable' not in alertType):
        alerttime = frameIdx
        alert = True

      print("=================Alert============================")
      print(alertType,":",alertText1,alertText2)

    #if collision 
    if len(collision_hist):
      hazard = True
      print(collision_hist[0],collision_hist[0].other_actor)
      # print(vehicle2)
      if collision_hist[0].other_actor.id == vehicle2.id: #collide with vehicle2:
        hazMsg ="collide with lead vihecle"
      hazardtime =frameIdx
      dRel = -0.1

    #if collision 
    laneInvasion_Flag = False
    if len(laneInvasion_hist)>Num_laneInvasion:
      # hazard = True
      laneInvasion_Flag =True
      Num_laneInvasion = len(laneInvasion_hist)
      print(Num_laneInvasion,laneInvasion_hist[-1],laneInvasion_hist[-1].crossed_lane_markings)
      # del(laneInvasion_hist[0])


    #lable hazard
    if dRel <0.5 and dRel != 0:
      if not hazard:
        hazard = True
        hazardtime =frameIdx
        hazMsg ="H1"

    

    #result print out
    # if rk.frame%PRINT_DECIMATION == 0:
    if rk.frame%PRINT_DECIMATION == 0 or dRel<1 and dRel != 0:
      print("Frame ID:",frameIdx,"frame: ", rk.frame,"engaged:", is_openpilot_engaged, "; throttle: ", round(vc.throttle, 3), "acc:" ,round(acceleration,2),round(throttle_out_hist/acceleration,2),"; steer(c/deg): ", round(vc.steer, 3), round(steer_out, 3), "; brake: ", round(vc.brake, 3),\
            "speed:",round(speed,2),'vLead:',round(vLead,2),"vRel",round(-vRel,2),"drel:",round(dRel,2),round(yRel,2),'Lanelines',yPos,ylaneLines,"FI:",FI_flage==1,"Hazard:",hazard)

    #result record in files
    pathleft = pathright = 0
    if len(ylaneLines)>2:
      pathleft = yPos- ylaneLines[1]
      pathright = ylaneLines[2]-yPos 
    if is_openpilot_engaged :#and (frameIdx%20==0 or (dRel<1 and dRel != 0)): #record every 20*10=0.2s
      fp_res.write("{},{},{},{},{},{},{},{},{},{},{},{},{},{},{},{},{},{},{},{},{}\n".format(frameIdx,0,speed,acceleration,steer_out,vc.throttle,vc.brake,vc.steer,dRel,-vRel,yRel,FI_flage==1,alert,hazard,altMsg,hazMsg, laneInvasion_Flag,yPos,ylaneLines,pathleft,pathright))

    rk.keep_time()
    # print(rk.frame)

    throttle_out_hist = vc.throttle


    #brake with hazard
    if hazard or FI_flage ==2 and speed<0.01:
      break

  #store alert,hazard message to a file, which will be stored in a summary file
  Alert_flag = len(alertType_list)>0 and 'startupMaster/permanent' not in alertType_list and 'buttonEnable/enable' not in alertType_list
  fp_temp = open("temp.txt",'w')
  fp_temp.write("{},{},{},{},{},{},{},{},{}".format("||".join(alertType_list),hazMsg,faulttime,alerttime,hazardtime, Alert_flag,hazard,fault_duration,Num_laneInvasion  ))
  fp_temp.close()

  # Clean up resources in the opposite order they were created.
  exit_event.set()
  for t in reversed(threads):
    t.join()
    # t.stop()
  gps.destroy()
  imu.destroy()
  camera.destroy()
  vehicle.destroy()
  colsensor.destroy()

  vehicle2.set_autopilot(False,8008)
  vehicle2.destroy()

  fp_res.close()
  # os.killpg(os.getpgid(os.getpid()), signal.SIGINT) #kill the remaining threads
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

  os.system('rm ./tools/sim/results/*')
  
  # make sure params are in a good state
  set_params_enabled()

  msg = messaging.new_message('liveCalibration')
  msg.liveCalibration.validBlocks = 20
  msg.liveCalibration.rpyCalib = [0.0, 0.0, 0.0]
  Params().put("CalibrationParams", msg.to_bytes())

  q: Any = Queue()
  # p = Process(target=bridge_keep_alive, args=(q,), daemon=True)
  # p.start()

  # # start input poll for keyboard
  # from lib.keyboard_ctrl import keyboard_poll_thread
  # p_keyboard = Process(target=keyboard_poll_thread, args=(q,), daemon=True)
  # p_keyboard.start()


  bridge_keep_alive(q)
  # p_keyboard.join()


  # if 0:#args.joystick:
  #   # start input poll for joystick
  #   from lib.manual_ctrl import wheel_poll_thread
  #   wheel_poll_thread(q)
  #   p.join()
  # else:
  #   # start input poll for keyboard
  #   from lib.keyboard_ctrl import keyboard_poll_thread
  #   keyboard_poll_thread(q)
