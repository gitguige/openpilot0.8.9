import os
import numpy as np
import random


def gen_add_code(trigger_code, trigger, t1, t2, variable, stuck_value, additional_code):
    assert(len(variable) == len(stuck_value))
    if trigger_code:
      code = trigger_code
    else:
      if len(trigger)>1:
        code = 'if %s>=%s and %s<=%s:' % \
            (trigger[0], t1, trigger[1], t2)
      else:
        code = 'if %s>=%s and %s<=%s:' % \
            (trigger[0], t1, trigger[0], t2)
    for v, s in zip(variable, stuck_value):
        l = '//%s+=%s' % (v,s)
        code = code + l
    code = code + additional_code
    return code

def gen_sub_code(trigger_code, trigger, t1, t2, variable, stuck_value, additional_code):
    assert(len(variable) == len(stuck_value))
    if trigger_code:
      code = trigger_code
    else:
      code = 'if %s>=%s and %s<=%s:' % \
            (trigger[0], t1, trigger[0], t2)
    for v, s in zip(variable, stuck_value):
        l = '//%s-=%s' % (v,s)
        code = code + l
    code = code + additional_code
    return code

def gen_none_code(trigger_code, trigger, t1, t2, additional_code):
    if trigger_code:
      code = trigger_code
    else:
      code = 'if %s>=%s and %s<=%s:' % \
            (trigger[0], t1, trigger[0], t2)
    l = '//none'
    code = code + l
    code = code + additional_code
    return code

def gen_uniform_rand_code(trigger_code, trigger, t1, t2, variable, d1, d2, additional_code):
    if trigger_code:
      code = trigger_code
    else:
      code = 'if %s>=%s and %s<=%s:' % \
            (trigger[0], t1, trigger[0], t2)
    for i in range(len(variable)):
      delta = random.uniform(d1,d2) + (i*3.7)
      l = '//%s+=(%s)' % (variable[i],str(delta))
      code = code + l
    code = code + additional_code
    return code

def gen_stuck_code(trigger_code, trigger, t1, t2, variable, stuck_value, additional_code):
    assert(len(variable) == len(stuck_value))
    if trigger_code:
      code = trigger_code
    else:
      code = 'if %s>=%s and %s<=%s:' % \
            (trigger[0], t1, trigger[0], t2)
    for v, s in zip(variable, stuck_value):
        l = '//%s=%s' % (v,s)
        code = code + l
    code = code + additional_code
    return code


### Write codes to fault library file
def write_to_file(fileName, code, param, exp_name, target_file, faultLoc):
    if os.path.isdir('fault_library') != True:
      os.makedirs('fault_library')
    fileName = 'fault_library/scenario_'+str(sceneNum)
    out_file = fileName+'.txt'
    param_file = fileName+'_params.csv'

    with open(out_file, 'w') as outfile:
        print out_file
        outfile.write('title:' + exp_name + '\n')
        outfile.write('location//' + target_file+ '//'+faultLoc + '\n')
        for i, line in enumerate(code):
            outfile.write('fault ' + str(i+1) + '//' + line + '\n')
        outfile.write('Total number of fault cases: '+str(i+1))

    with open(param_file, 'w') as outfile:
        for i, line in enumerate(param):
            outfile.write(str(i) + ',' + line + '\n')

    with open('run_fault_inject_campaign.sh', 'a+') as runFile:
        runFile.write('python run.py '+fileName+'\n')

### Write codes to fault library file -- for vision effects
def write_to_vision_file(fileName, code, param, exp_name, target_file, faultLoc):
    if os.path.isdir('fault_library') != True:
      os.makedirs('fault_library')
    effect = fileName
    fileName = 'fault_library/scenario_'+str(sceneNum)
    out_file = fileName+'.txt'
    param_file = fileName+'_params.csv'

    with open(out_file, 'w') as outfile:
        print out_file
        outfile.write('title:' + exp_name + '\n')
        outfile.write('location//' + target_file+ '//'+faultLoc + '\n')
        for i, line in enumerate(code):
            outfile.write('fault ' + str(i+1) + '//' + line + '\n')
        outfile.write('Total number of fault cases: '+str(i+1))

    with open(param_file, 'w') as outfile:
        for i, line in enumerate(param):
            outfile.write(str(i) + ',' + line + '\n')


    with open('run_fault_inject_campaign.sh', 'a+') as runFile:
      for thickness in range(1,11):
        if os.path.isdir('../output_files/'+str(sceneNum)+'_vision_'+effect+'/'+str(thickness)) != True:
          os.makedirs('../output_files/'+str(sceneNum)+'_vision_'+effect+'/'+str(thickness))
        runFile.write('./run_matlab_openpilot.sh '+effect+' '+str(thickness)+'\n')
        runFile.write('python run.py '+fileName+'\n')
        runFile.write('cp -R '+'../output_files/'+exp_name+' '+'../output_files/'+str(sceneNum)+'_vision_'+effect+'/'+str(thickness)+'/\n')


###########################################################
### d_rel-add-incRADAR-H1
def gen_rel_dist_add_fault_plant(sceneNum):
    title = str(sceneNum)+'_d_rel-add-incRADAR-H1'
    faultLibFile = 'fault_library/dRelPlantRad'
    fileLoc = 'selfdrive/test/plant/plant.py'
    faultLoc = '#radar_dRel:HOOK#'
    trigger = ['frameIdx']
    trigger_code = ['if headway_time<=2.0 and RSpeed<=0:', 'if headway_time<=2.0 and RSpeed>0:', 'if headway_time>2.0 and RSpeed>0:','if headway_time>2.0 and RSpeed<=0:']
    code = []
    param = []
    variable = ['radar_dRel']
    deltaRange = np.arange(15,190,10)
    invRange = np.arange(201,256,10)

    for trig in np.arange(0,len(trigger_code)):
        for dt in [30.0]:
          t2 = dt
          for d in deltaRange:
            delta = random.randint(d,d+9)
            t1 = random.randint(2,29)
            #code.append(gen_add_code(trigger_code, trigger, t1, t2, variable, [delta], '//if '+variable[0]+'>=255:'+'//  '+variable[0]+'= 254'))
            code.append(gen_add_code('', trigger, t1*100., t2*100., variable, [delta], ''))
            param.append(','.join(['relative distance',str(t1),str(dt),str(delta)]))

        for dt in [30.0]:
          t2 = dt
          for d in invRange:
            delta = random.randint(d,d+9)
            t1 = random.randint(2,29)
            #code.append(gen_add_code(trigger_code, trigger, t1, t2, variable, [delta], '//if '+variable[0]+'>=255:'+'//  '+variable[0]+'= 254'))
            code.append(gen_add_code('', trigger, t1*100., t2*100., variable, [delta], ''))
            param.append(','.join(['relative distance',str(t1),str(dt),str(delta)]))

    write_to_file(faultLibFile, code, param, title, fileLoc, faultLoc)

### v_rel-add-incRADAR-H1
def gen_rel_vel_add_fault_plant(sceneNum):
    title = str(sceneNum)+'_v_rel-add-incRADAR-H1'
    faultLibFile = 'fault_library/vRelPlant'
    fileLoc = 'selfdrive/test/plant/plant.py'
    faultLoc = '#radar_dRel:HOOK#'
    trigger = ['frameIdx']
    trigger_code = ['if headway_time<=2.0 and RSpeed<=0:', 'if headway_time<=2.0 and RSpeed>0:', 'if headway_time>2.0 and RSpeed>0:','if headway_time>2.0 and RSpeed<=0:']
    code = []
    param = []
    variable = ['v_rel']
    deltaRange = np.arange(10,61,10)
    
    for trig in np.arange(0,len(trigger_code)):
        for dt in [30.0]:
          t2 = dt
          for d in deltaRange:
            t1 = random.randint(2,29)
            delta = random.randint(d,d+9)
            if delta > 60:
              delta = 60
            delta = delta*0.44704    # 1MPH = 0.44704 m/s
            code.append(gen_add_code('', trigger, t1*100., t2*100., variable, [delta], ''))
            param.append(','.join(['relative speed',str(t1),str(dt),str(delta)]))

    write_to_file(faultLibFile, code, param, title, fileLoc, faultLoc)

### d_rel-sub-incRADAR-H2
def gen_rel_dist_sub_fault_plant(sceneNum):
    title = str(sceneNum)+'_d_rel-sub-incRADAR-H2'
    faultLibFile = 'fault_library/dRelPlantRad'
    fileLoc = 'selfdrive/test/plant/plant.py'
    faultLoc = '#radar_dRel:HOOK#'
    trigger = ['frameIdx']
    trigger_code = ['if headway_time>2.0 and RSpeed<=0:','if headway_time<=2.0 and RSpeed<=0:', 'if headway_time<=2.0 and RSpeed>0:', 'if headway_time>2.0 and RSpeed>0:']
    code = []
    param = []
    variable = ['radar_dRel']
    deltaRange = np.arange(10,255,10)
    for trig in np.arange(0,len(trigger_code)):
      for d in deltaRange:
          for dt in [30.]:
            t2 = dt
            t1 = random.randint(2,29)
            delta = random.randint(d,d+9)
            code.append(gen_sub_code('',trigger, t1*100., t2*100., variable, [delta], '//if '+variable[0]+'<0:'+'//  '+variable[0]+'= 0'))
            param.append(','.join(['relative distance',str(t1),str(dt),str(delta)]))

    write_to_file(faultLibFile, code, param, title, fileLoc, faultLoc)

### v_rel-sub-incRADAR-H2
def gen_rel_vel_sub_fault_plant(sceneNum):
    title = str(sceneNum)+'_v_rel-sub-incRADAR-H2'
    faultLibFile = 'fault_library/vRelPlant'
    fileLoc = 'selfdrive/test/plant/plant.py'
    faultLoc = '#radar_dRel:HOOK#'
    trigger = ['frameIdx']
    trigger_code = ['if headway_time>2.0 and RSpeed<=0:','if headway_time<=2.0 and RSpeed<=0:', 'if headway_time<=2.0 and RSpeed>0:', 'if headway_time>2.0 and RSpeed>0:']
    code = []
    param = []
    variable = ['v_rel']
    deltaRange = np.arange(10,61,10)
    for trig in np.arange(0,len(trigger_code)):
      for d in deltaRange:
          for dt in [30.]:
            t2 = dt
            delta = random.randint(d,d+9)
            t1 = random.randint(2,29)
            if delta > 60:
              delta = 60
            delta = delta*0.44704    # 1MPH = 0.44704 m/s
            code.append(gen_sub_code('', trigger, t1*100., t2*100., variable, [delta], ''))
            param.append(','.join(['relative speed',str(t1),str(dt),str(delta)]))

    write_to_file(faultLibFile, code, param, title, fileLoc, faultLoc)

### radar-none-incRADAR-H1
def gen_radar_jamming_fault_plant_H1(sceneNum):
    title = str(sceneNum)+'_radar-none-incRADAR-H1'
    faultLibFile = 'fault_library/radJamPlant'
    fileLoc = 'selfdrive/test/plant/plant.py'
    faultLoc = '#radar_none:HOOK#'
    trigger = ['frameIdx']
    trigger_code = ['if headway_time>2.0 or RSpeed>0:', 'if headway_time>2.0 or RSpeed<=0:', 'if headway_time<=2.0 or RSpeed<=0:']  # reverse of actual trigger
    code = []
    param = []
    variable = []

    for trig in np.arange(0,len(trigger_code)):
        for dt in [0.0]:
          t1 = random.randint(2,29)
          t2 = dt
          code.append(gen_none_code('', trigger, t2*100., t1*100., ''))
          param.append(','.join(['radar jamming',str(t1),str(dt),'none']))

    write_to_file(faultLibFile, code, param, title, fileLoc, faultLoc)

### radar-none-incRADAR-H2
def gen_radar_jamming_fault_plant_H2(sceneNum):
    title = str(sceneNum)+'_radar-none-incRADAR-H2'
    faultLibFile = 'fault_library/radJamPlant'
    fileLoc = 'selfdrive/test/plant/plant.py'
    faultLoc = '#radar_none:HOOK#'
    trigger = ['frameIdx']
    trigger_code = ['if headway_time<=2.0 or RSpeed>0:']
    code = []
    param = []
    variable = []
    for trig in np.arange(0,len(trigger_code)):
        for dt in [0.0]:
          t1 = random.randint(2,29)
          t2 = dt
          code.append(gen_none_code('', trigger, t2*100., t1*100., ''))
          param.append(','.join(['radar jamming',str(t1),str(dt),'none']))

    write_to_file(faultLibFile, code, param, title, fileLoc, faultLoc)

### curr_sp-sub-incProcPlant-H1
def gen_curr_sp_sub_fault_plant(sceneNum):
    title = str(sceneNum)+'_curr_sp-sub-incProcPlant-H1'
    faultLibFile = 'fault_library/vCurrSpPlant'
    fileLoc = 'selfdrive/test/plant/plant.py'
    faultLoc = '#speed:HOOK#'
    trigger = ['frameIdx']
    trigger_code = ['if headway_time<=2.0 and RSpeed<=0:', 'if headway_time<=2.0 and RSpeed>0:', 'if headway_time>2.0 and RSpeed>0:', 'if headway_time>2.0 and RSpeed<=0:']
    code = []
    param = []
    variable = ['speed2send']
    deltaRange = np.arange(10,61,10)
    
    for trig in np.arange(0,len(trigger_code)):
        for dt in [30.0]:
          t2 = dt
          for d in deltaRange:
            delta = random.randint(d,d+9)
            if delta > 60:
              delta = 60
            delta = delta*0.44704    # 1MPH = 0.44704 m/s
            t1 = random.randint(2,29)
            code.append(gen_sub_code('', trigger, t1*100., t2*100., variable, [delta], '//if '+variable[0]+'<0:'+'//  '+variable[0]+'= 0'))
            param.append(','.join(['current speed',str(t1),str(dt),str(delta)]))

    write_to_file(faultLibFile, code, param, title, fileLoc, faultLoc)

### curr_sp-add-incProcPlant-H2
def gen_curr_sp_add_fault_plant(sceneNum):
    title = str(sceneNum)+'_curr_sp-add-incProcPlant-H2'
    faultLibFile = 'fault_library/vCurrSpPlant'
    fileLoc = 'selfdrive/test/plant/plant.py'
    faultLoc = '#speed:HOOK#'
    trigger = ['frameIdx']
    trigger_code = ['if headway_time>2.0 and RSpeed<=0:','if headway_time<=2.0 and RSpeed<=0:', 'if headway_time<=2.0 and RSpeed>0:', 'if headway_time>2.0 and RSpeed>0:']
    code = []
    param = []
    variable = ['speed2send']
    deltaRange = np.arange(10,61,10)

    for trig in np.arange(0,len(trigger_code)):
      for d in deltaRange:
          for dt in [30.]:
            t2 = dt
            delta = random.randint(d,d+9)
            if delta > 60:
              delta = 60
            delta = delta*0.44704    # 1MPH = 0.44704 m/s
            t1 = random.randint(2,29)
            code.append(gen_add_code('', trigger, t1*100., t2*100., variable, [delta], '//if '+variable[0]+'>=85.0:'+'//  '+variable[0]+'= 85.0'))
            param.append(','.join(['current speed',str(t1),str(dt),str(delta)]))

    write_to_file(faultLibFile, code, param, title, fileLoc, faultLoc)

### md-rand-incProcPlant-H3
def gen_md_rand_val_plant(lane,sceneNum):
    title = str(sceneNum)+'_'+lane+'Lane-rand-incProcPlant-H3'
    faultLibFile = 'fault_library/mdPlant_'+lane
    fileLoc = 'selfdrive/test/plant/maneuver.py'
    faultLoc = '#md:HOOK#'
    trigger = ['self.frameIdx']
    trigger_code = ['if headway_time<=2.0 and RSpeed>=0:', 'if headway_time>2.0 and RSpeed<=0:','if headway_time<=2.0 and RSpeed<=0:','if headway_time>2.0 and RSpeed>0:']
    code = []
    param = []
    if lane.lower()=='left':
      variable = ['self.lLane']
    elif lane.lower()=='right':
      variable = ['self.rLane']
    else:
      variable = ['self.lLane','self.rLane']
    deltaRange = np.arange(-2.5,2.5,0.5)

    for trig in np.arange(0,len(trigger_code)):
        for dt in [30.0]:
          t2 = dt
          for d1 in deltaRange:
            d2 = d1+1
            t1 = random.randint(2,29)
            code.append(gen_uniform_rand_code('', trigger, t1*100., t2*100., variable, d1, d2, ''))
            param.append(','.join(['path model',str(t1),str(dt),str(d1),str(d2)]))

    write_to_file(faultLibFile, code, param, title, fileLoc, faultLoc)

### angSteer-add-incProcPlant-H3
def gen_angle_steer_add_plant(sceneNum):
    title = str(sceneNum)+'_angSteer-add-incProcPlant-H3'
    faultLibFile = 'fault_library/angSteerPlant'
    fileLoc = 'selfdrive/test/plant/plant.py'
    faultLoc = '#angle_steer:HOOK#'
    trigger = ['frameIdx']
    trigger_code = ['if headway_time>2.0 and RSpeed>=0:','if headway_time<=2.0 and RSpeed<=0:', 'if headway_time<=2.0 and RSpeed>0:','if headway_time>2.0 and RSpeed>0:']
    code = []
    param = []
    variable = ['angle_steer2send']
    deltaRange = np.arange(-45,46,10)

    for trig in np.arange(0,len(trigger_code)):
        for dt in [30.0]:
          t2 = dt
          for d in deltaRange:
            delta = random.randint(d,d+9)
            if d > 45:
              alpha = 45*3.1416/180.0
            else:
              alpha = delta*3.1416/180.0
            t1 = random.randint(2,29)
            code.append(gen_add_code('', trigger, t1*100., t2*100., variable, ['('+str(alpha)+')'], ''))
            param.append(','.join(['steer angle',str(t1),str(dt),str(alpha)]))

    write_to_file(faultLibFile, code, param, title, fileLoc, faultLoc)

### vision-none-miscommVisPlant-H3
def gen_vision_miscomm_fault_plant(sceneNum):
    title = str(sceneNum)+'_vision-none-miscommVisPlant-H3'
    faultLibFile = 'fault_library/visMiscommPlant'
    fileLoc = 'selfdrive/test/plant/plant.py'
    faultLoc = '#md_none:HOOK#'
    trigger = ['frameIdx']
    trigger_code =  ['if headway_time>2.0 or RSpeed<0:','if headway_time>2.0 or RSpeed>0', 'if headway_time<=2.0 or RSpeed<=0', 'if headway_time<=2.0 or RSpeed>0']
    code = []
    param = []
    variable = []

    for trig in np.arange(0,len(trigger_code)):
        for dt in [0.0]:
          t2 = dt
          t1 = random.randint(2,29)
          code.append(gen_none_code('', trigger, t2*100., t1*100., ''))
          param.append(','.join(['vision miscomm',str(t1),str(dt),'none']))

    write_to_file(faultLibFile, code, param, title, fileLoc, faultLoc)

### vision-effect-noisyInputManeuver-H3
def gen_vision_noisyInput_fault_Maneuver(effect, sceneNum):
    title = str(sceneNum)+'_vision-effect-noisyInputManeuver-H3'
    faultLibFile = ''
    fileLoc = 'selfdrive/test/plant/maneuver.py'
    faultLoc = '#visionFault:HOOK#'
    trigger = ['self.frameIdx']
    trigger_code = ['if headway_time<=2.5 and RSpeed>=0:', 'if headway_time>2.5 and RSpeed>0:','if headway_time>2.5 and RSpeed<=0:','if headway_time<=2.5 and RSpeed<0:']
    code = []
    param = []
    #variable = ['left_line','right_line']
    #deltaRange = ['lanes[0]','lanes[1]']
    variable = ['self.effect', 'self.thickness']

    if effect <7:
      range_th = range(1,11)
    elif effect == 7:
      range_th = range(3,7)
    elif effect == 8:
      range_th = [3,5,7]
    elif effect == 9:
      range_th = [3,5]

    for trig in np.arange(0,len(trigger_code)):
        for dt in [30.0]:
          for th in range_th:
            t2 = dt
            t1 = random.randint(2,29)
            code.append(gen_stuck_code('', trigger, t1*100., t2*100., variable, [str(effect), str(th)], ''))
            param.append(','.join(['vision noisyInput',str(t1),str(dt),'none']))

    write_to_file(faultLibFile, code, param, title, fileLoc, faultLoc)

### d_rel-add-incVision-H1
def gen_vision_dRel_add_fault_plant(sceneNum):
    title = str(sceneNum)+'_d_rel-add-incVision-H1'
    faultLibFile = 'fault_library/dRelPlantVis'
    fileLoc = 'selfdrive/test/plant/plant.py'
    faultLoc = '#vision_dRel:HOOK#'
    trigger = ['frameIdx']
    trigger_code = ['if headway_time<=2.0 and RSpeed<=0:', 'if headway_time<=2.0 and RSpeed>0:', 'if headway_time>2.0 and RSpeed>0:','if headway_time>2.0 and RSpeed<=0:']
    code = []
    param = []
    variable = ['vision_dRel']
    deltaRange = np.arange(15,255,10)

    for trig in np.arange(0,len(trigger_code)):
        for dt in [30.0]:
          t2 = dt
          for d in deltaRange:
            delta = random.randint(d,d+9)
            t1 = random.randint(2,29)
            #code.append(gen_add_code(trigger_code, trigger, t1, t2, variable, [delta], '//if '+variable[0]+'>=255:'+'//  '+variable[0]+'= 254'))
            code.append(gen_add_code('', trigger, t1*100., t2*100., variable, [delta], ''))
            param.append(','.join(['relative distance',str(t1),str(dt),str(delta)]))

    write_to_file(faultLibFile, code, param, title, fileLoc, faultLoc)

### d_rel-sub-incVision-H2
def gen_vision_dRel_sub_fault_plant(sceneNum):
    title = str(sceneNum)+'_d_rel-sub-incVision-H2'
    faultLibFile = 'fault_library/dRelPlantVis'
    fileLoc = 'selfdrive/test/plant/plant.py'
    faultLoc = '#vision_dRel:HOOK#'
    trigger = ['frameIdx']
    trigger_code = ['if headway_time>2.0 and RSpeed<=0:','if headway_time<=2.0 and RSpeed<=0:', 'if headway_time<=2.0 and RSpeed>0:', 'if headway_time>2.0 and RSpeed>0:']
    code = []
    param = []
    variable = ['vision_dRel']
    deltaRange = np.arange(10,255,10)

    for trig in np.arange(0,len(trigger_code)):
      for d in deltaRange:
          for dt in [30.0]:
            t2 = dt
            delta = random.randint(d,d+9)
            t1 = random.randint(2,29)
            code.append(gen_sub_code('',trigger, t1*100., t2*100., variable, [delta], '//if '+variable[0]+'<0:'+'//  '+variable[0]+'= 0'))
            param.append(','.join(['relative distance',str(t1),str(dt),str(delta)]))

    write_to_file(faultLibFile, code, param, title, fileLoc, faultLoc)

### d_rel-add-incRadVis-H1
def gen_RadVis_dRel_add_fault_plant(sceneNum):
    title = str(sceneNum)+'_d_rel-add-incRadVis-H1'
    faultLibFile = 'fault_library/dRelPlantRadVis'
    fileLoc = 'selfdrive/test/plant/plant.py'
    faultLoc = '#RadVis_dRel:HOOK#'
    trigger =  ['frameIdx']
    trigger_code = ['if headway_time<=2.0 and RSpeed<=0:', 'if headway_time<=2.0 and RSpeed>0:', 'if headway_time>2.0 and RSpeed>0:', 'if headway_time>2.0 and RSpeed<=0:']
    code = []
    param = []
    variable = ['d_rel']
    deltaRange = np.arange(15,255,10)

    for trig in np.arange(0,len(trigger_code)):
        for dt in [30.0]:
          t2 = dt
          for d in deltaRange:
            delta = random.randint(d,d+9)
            t1 = random.randint(2,29)
            #code.append(gen_add_code(trigger_code, trigger, t1, t2, variable, [delta], '//if '+variable[0]+'>=255:'+'//  '+variable[0]+'= 254'))
            code.append(gen_add_code('', trigger, t1*100., t2*100., variable, [delta], ''))
            param.append(','.join(['relative distance',str(t1),str(dt),str(delta)]))

    write_to_file(faultLibFile, code, param, title, fileLoc, faultLoc)

### d_rel-sub-incRadVis-H2
def gen_RadVis_dRel_sub_fault_plant(sceneNum):
    title = str(sceneNum)+'_d_rel-sub-incRadVis-H2'
    faultLibFile = 'fault_library/dRelPlantRadVis'
    fileLoc = 'selfdrive/test/plant/plant.py'
    faultLoc = '#RadVis_dRel:HOOK#'
    trigger =  ['frameIdx']
    trigger_code = ['if headway_time>2.0 and RSpeed<=0:','if headway_time<=2.0 and RSpeed<=0:', 'if headway_time<=2.0 and RSpeed>0:', 'if headway_time>2.0 and RSpeed>0:']
    code = []
    param = []
    variable = ['d_rel']
    deltaRange = np.arange(10,255,10)
    for trig in np.arange(0,len(trigger_code)):
      for d in deltaRange:
          for dt in [30.0]:
            t2 = dt
            delta = random.randint(d,d+9)
            t1 = random.randint(2,29)
            code.append(gen_sub_code('',trigger, t1*100., t2*100., variable, [delta], '//if '+variable[0]+'<0:'+'//  '+variable[0]+'= 0'))
            param.append(','.join(['relative distance',str(t1),str(dt),str(delta)]))

    write_to_file(faultLibFile, code, param, title, fileLoc, faultLoc)


##########################################
###_main_###

with open('run_fault_inject_campaign.sh', 'w') as runFile:
    runFile.write('#Usage: python run.py target_fault_library\n')

scenarios = {

1 : gen_rel_dist_add_fault_plant,
2 : gen_rel_vel_add_fault_plant,
3 : gen_rel_dist_sub_fault_plant,
4 : gen_rel_vel_sub_fault_plant,
5 : gen_radar_jamming_fault_plant_H1,
6 : gen_radar_jamming_fault_plant_H2,
9 : gen_curr_sp_sub_fault_plant,
12 : gen_curr_sp_add_fault_plant,
13 : gen_md_rand_val_plant,
14 : gen_md_rand_val_plant,
15 : gen_md_rand_val_plant,
16 : gen_angle_steer_add_plant,
34 : gen_vision_miscomm_fault_plant,
35 : gen_vision_noisyInput_fault_Maneuver,
36 : gen_vision_noisyInput_fault_Maneuver,
37 : gen_vision_noisyInput_fault_Maneuver,
38 : gen_vision_noisyInput_fault_Maneuver,
39 : gen_vision_dRel_add_fault_plant,
40 : gen_vision_dRel_sub_fault_plant,
41 : gen_RadVis_dRel_add_fault_plant,
42 : gen_RadVis_dRel_sub_fault_plant,
43 : gen_vision_noisyInput_fault_Maneuver,
44 : gen_vision_noisyInput_fault_Maneuver,
45 : gen_vision_noisyInput_fault_Maneuver,
46 : gen_vision_noisyInput_fault_Maneuver,
47 : gen_vision_noisyInput_fault_Maneuver
}

lanes = ['left','right','both']  # 'left','right','both'
poly = ['p_path','left','right','d_path']  # 'p_path','left','right','d_path'
#effects = ['rain', 'fog', 'snow', 'occlusion']
effects = [1,2,3,4,5,6,7,8,9]

for sceneNum in [1,2,3,4,5,6,9,12,13,14,15,16,34,39,40,41,42]: # experiments without the vision
#for sceneNum in [35,36,37,38,43,44,45,46,47]: # for testing the faults in input images
#for sceneNum in [1,2,3,4,5,6,9,12,13,14,15,16,34,35,36,37,38,39,40,41,42,43,44,45,46,47]: # for testing the faults in inputs
# for sceneNum in [44,45,46,47]:
  print sceneNum
  cmd = 'cp '+ 'fault_library/scenario_'+str(sceneNum)+'.txt '+'fault_library/scenario_'+str(sceneNum)+'_prev.txt'
  os.system(cmd)
  if sceneNum >= 13 and sceneNum <=15:
    scenarios[sceneNum](lanes[sceneNum-13],sceneNum)
  elif sceneNum >= 28 and sceneNum <=31:
    scenarios[sceneNum](poly[sceneNum-28],sceneNum)
  elif sceneNum >= 35 and sceneNum <=38:
    scenarios[sceneNum](effects[sceneNum-35],sceneNum)
  elif sceneNum >= 43 and sceneNum <=47:
    scenarios[sceneNum](effects[sceneNum+4-43],sceneNum)
  else:
    scenarios[sceneNum](sceneNum)








