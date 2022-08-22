from curses.ascii import FF
import os
import numpy as np
import random

	
def gen_add_code(trigger_STPA,trigger, trigger_time,stop_time, variable, stuck_value, additional_code=''):
	if trigger_STPA:
		code = trigger_STPA
	else:
		code = 'if %s>=%s and %s<%s:'%(trigger,trigger_time,trigger,stop_time)
	l = '//%s+=%s' % (variable,stuck_value)
	code = code + l
	return code + additional_code


def gen_sub_code(trigger_STPA,trigger, trigger_time, stop_time,variable, stuck_value,additional_code=''):
	if trigger_STPA:
		code = trigger_STPA
	else:
		code = 'if %s>=%s and %s<%s:'%(trigger,trigger_time,trigger,stop_time)
	l = '//%s-=%s' % (variable,stuck_value)
	code = code + l
	return code + additional_code

	
def gen_stuck_code(trigger_STPA,trigger, trigger_time, stop_time,variable, stuck_value,additional_code=''):
	if trigger_STPA:
		code = trigger_STPA
	else: #random
		code = 'if %s>=%s and %s<%s:'%(trigger,trigger_time,trigger,stop_time)
	l = '//%s=%s' % (variable,stuck_value)
	code = code + l
	return code + additional_code
######################################################################

	
### Write codes to fault library file
def write_to_file(code, exp_name, target_file, faultLoc):
	if os.path.isdir('fault_library_monitor_V2') != True:
		os.makedirs('fault_library_monitor_V2')
	fileName = 'fault_library_monitor_V2/scenario_'+str(sceneNum)
	out_file = fileName+'.txt'
	#param_file = fileName+'_params.csv'
	i=0

	with open(out_file, 'w') as outfile:
		#print out_file
		outfile.write('title:' + exp_name + '\n')
		outfile.write('location//' + target_file+ '//'+faultLoc + '\n')
		for i, line in enumerate(code):
			outfile.write('fault ' + str(i+1) + '//' + line + '\n')
		outfile.write('Total number of fault cases: '+str(i+1))

	with open('run_fault_inject_monitor_V2_campaign.sh', 'a+') as runFile:
		runFile.write('python3 run.py '+fileName+'\n')

############################################################################

def write_to_file_STPA(code, exp_name, target_file, faultLoc):
	if os.path.isdir('fault_library_monitor_V2_STPA') != True:
		os.makedirs('fault_library_monitor_V2_STPA')
	fileName = 'fault_library_monitor_V2_STPA/scenario_'+str(sceneNum)
	out_file = fileName+'.txt'
	#param_file = fileName+'_params.csv'
	i=0

	with open(out_file, 'w') as outfile:
		#print out_file
		outfile.write('title:' + exp_name + '\n')
		outfile.write('location//' + target_file+ '//'+faultLoc + '\n')
		for i, line in enumerate(code):
			outfile.write('fault ' + str(i+1) + '//' + line + '\n')
		outfile.write('Total number of fault cases: '+str(i+1))

	with open('run_fault_inject_monitor_V2_STPA_campaign.sh', 'a+') as runFile:
		runFile.write('python3 run.py '+fileName+'\n')

def write_both_to_file(code,code_STPA, title, fileLoc, faultLoc):
	write_to_file(code, title, fileLoc, faultLoc)
	write_to_file_STPA(code_STPA, title, fileLoc, faultLoc)	
#################################################################################3

##########################################################################################################
def gen_code_common_fixedduration(title,fileLoc,faultLoc,variable,newvalue,newvalue2=0,early_start=False,trigger_STPA_list=['if xxxxx:'],additional_code='',FI_H3_combine_enable = False,change_duraiton=False,change_duraitont0=False,RepeatTimes=1):
		
	title1 = ""
	trigger = 'frameIdx' #trigger_random
	code = []
	code_STPA=[]
	#param = []
	# N_duration =4
	per_time_range = 2
	time_partition = np.arange(5,40,per_time_range) #0-40 changed to 5-40, don't FI before successfully initialized and speed up
	valuelist = []
	valuelist.append(newvalue)
	if newvalue2:
		valuelist.append(newvalue2)

	FI_Type_Steer = ["//FI_Type |= 0x04","//FI_Type |= 0x08"]
	# additional_code='//brake_out=0//FI_flag=1'
	# additional_code='//FI_flag=1'

	for repeat in range(RepeatTimes):
		for valueitem in valuelist:
			#random FI
			for tindex in [1,1]+list(range(len(time_partition))): #20
				trigger_time = random.randint(time_partition[tindex]*100,time_partition[tindex]*100+per_time_range*100-1) #t
				if change_duraitont0: #randm duration and start time, fixed value : S21-S26
					for t_duration in range(50,250,20):  #10
						if FI_H3_combine_enable == True:
							additional_code_combine = FI_Type_Steer[int(round(random.random()))]
						else:
							additional_code_combine = ""
						duration = random.randint(t_duration,t_duration+19)
						additional_code1 = additional_code + "//FI_duration = {}".format(duration) + additional_code_combine
						stop_time = trigger_time + duration
						code.append(gen_stuck_code('',trigger, trigger_time,stop_time, variable, valueitem,additional_code=additional_code1))
				else: #random start time
					if change_duraiton: # radndom t0* random duration * random value = 5*4 * 10 = 200: S11-S16
						title1 = title[:-8] + "totally"
						if tindex%4 == 0: #5
							for t_duration in range(50,250,50): # 4
								duration = random.randint(t_duration,t_duration+49)
								for t_percent in range(1,100,10): #0~100%
									if FI_H3_combine_enable == True:
										additional_code_combine = FI_Type_Steer[int(round(random.random()))]
									else:
										additional_code_combine = ""
									FI_percent = random.randint(t_percent,t_percent+9)
									additional_code1 = additional_code + "//FI_duration = {}//FI_percent = {}".format(duration,FI_percent) + additional_code_combine
									stop_time = trigger_time + duration
									code.append(gen_stuck_code('',trigger, trigger_time,stop_time, variable, valueitem,additional_code=additional_code1))
					else: # randm start time, Fixed duration 2.5s, fixed value: S1-S6
						if FI_H3_combine_enable == True:
							additional_code_combine = FI_Type_Steer[int(round(random.random()))]
						else:
							additional_code_combine = ""
						additional_code1 = additional_code + "//FI_duration = {}".format(250) + additional_code_combine
						stop_time = trigger_time + 250 
						code.append(gen_stuck_code('',trigger, trigger_time,stop_time, variable, valueitem,additional_code=additional_code1))

			#STPA FI
			if FI_H3_combine_enable == True:
				additional_code_combine = "//FI_Context_H3_combine_enable = 1"
			else:
				additional_code_combine = ""
			for trigger_STPA in trigger_STPA_list:
				if change_duraiton: #random duration + STPA start time
					for duration in range(50,250,10): # 20, S11-S16
						additional_code1 = additional_code + "//FI_duration = {}".format(random.randint(duration,duration+10)) + additional_code_combine
						code_STPA.append(gen_stuck_code(trigger_STPA,trigger, trigger_time*100,stop_time*100, variable, valueitem,additional_code=additional_code1))
				else:
					for loop_repeat in range(20): #repeat for xx times: S1-S6
						additional_code1 = additional_code + additional_code_combine
						code_STPA.append(gen_stuck_code(trigger_STPA,trigger, trigger_time*100,stop_time*100, variable, valueitem,additional_code=additional_code1))
		
	#update title is title1 is not null
	if len(title1): 
		title = title1 
	write_both_to_file(code,code_STPA, title, fileLoc, faultLoc)

def gen_add_code_common_multiplestoptime(title,fileLoc,faultLoc,variable,direction,early_start=False): #direction: 0-decreade, 1-increase
		
	trigger = 'frameIdx'
	# trigger_time = 10 # 10 is an arbitrary number, I want the fault be injected after 10th iteration
	trigger_STPA = 'if xxxxx:' #wait to change to 27 rules in the context table
	code = []
	code_STPA=[]
	#param = []
	N_duration =4
	time_partition = np.arange(2,21,2) #2,4,6,8,10 ..20# Num=10

	additional_code=''
	if direction == True:
		func = gen_add_code
	else:
		func = gen_sub_code
		additional_code='//if '+variable+'<0:'+'//  '+variable+'= 0'

	if 'v_rel' in variable: #[10,61]
		factor =0.44704    # 1MPH = 0.44704 m/s # 1mph = 05 m/s
		daterange=[16*factor,24*factor,32*factor,40*factor,48*factor,56*factor]
	else:
		daterange=[32,64,96,128,160,192] #meters
	
	for gain in daterange: #single or multiple bitflips
		for tindex in range(len(time_partition)): #10
			trigger_time = random.randint(time_partition[tindex],time_partition[tindex]+1) #t
			dt = int((28 - trigger_time)/N_duration) #divided into 4 parts
			for i in range(1,1+N_duration): #
				stop_time = random.randint(trigger_time+dt*i+1,trigger_time+dt*i+dt) #hong long fault will last, at least one iteration
				if stop_time >30: #make sure the stop time is no more than 29
					stop_time = 30

				code.append(func('',trigger, trigger_time*100,stop_time*100, variable, gain,additional_code))
				code_STPA.append(func(trigger_STPA,trigger, trigger_time*100,stop_time*100, variable, gain,additional_code))
				#param.append(','.join(['relative distance',str(t1),str(dt),str(delta)]))

	write_both_to_file(code,code_STPA, title, fileLoc, faultLoc)



def gen_lostconnection_hold_dRel(sceneNum): #S9
	title = str(sceneNum)+'_lostconnection_hold_dRel'
	#faultLibFile = 'fault_library_monitor_V2/dRelPlantRad'
	fileLoc = 'selfdrive/test/plant/plant.py'
	faultLoc = '#holdfault:HOOK#'
	variable = 'radar_dRel_refresh'
	newvalue = 0

	gen_code_common_fixedduration(title,fileLoc,faultLoc,variable,newvalue,early_start=True)


	
def gen_bitflip_add_dRel(sceneNum): #S12
	title = str(sceneNum)+'_bitflip_add_dRel'

	# fileLoc = 'updated_ct_script_iob_based.py'
	# faultLoc = '#rate:HOOK#'
	variable = 'radar_dRel'

	fileLoc = 'selfdrive/test/plant/plant.py'
	faultLoc = '#radar_dRel:HOOK#'

	gen_add_code_common_multiplestoptime(title,fileLoc,faultLoc,variable, True)

def gen_bitflip_sub_dRel(sceneNum): #S13
	title = str(sceneNum)+'_bitflip_sub_dRel'

	variable = 'radar_dRel'

	fileLoc = 'selfdrive/test/plant/plant.py'
	faultLoc = '#radar_dRel:HOOK#'

	gen_add_code_common_multiplestoptime(title,fileLoc,faultLoc,variable, False,early_start=True)

##########################################################################################
def gen_max_throttle(sceneNum):#S1
	title = str(sceneNum)+'_max_throttle'
	fileLoc = 'tools/sim/bridge.py'
	faultLoc = '#throttle:HOOK#'
	variable = 'FI_flag'
	newvalue = '1'
	# newvalue2 = '4'
	additional_code='//FI_Type |= 0x01'

	# trigger_code_list = ['if headway_time<=2.0 and RSpeed<=0 and vLead!=0:', 'if headway_time<=2.0 and RSpeed>0 and vLead!=0:', 'if headway_time>2.0 and RSpeed>0 and vLead!=0:','if headway_time>2.0 and RSpeed<=0 and vLead!=0:']
	trigger_STPA_list = ['if headway_time<=2.0 and RSpeed>0 and vLead!=0:']#, 'if headway_time<=2.0 and RSpeed<=0 and vLead!=0:']

	gen_code_common_fixedduration(title,fileLoc,faultLoc,variable, newvalue,trigger_STPA_list=trigger_STPA_list,additional_code=additional_code)

def gen_max_brake(sceneNum):#S2
	title = str(sceneNum)+'_max_brake'
	fileLoc = 'tools/sim/bridge.py'
	faultLoc = '#throttle:HOOK#'
	variable = 'FI_flag'
	newvalue = '1'
	# newvalue2 = '4'
	additional_code='//FI_Type |= 0x02'

	# trigger_code_list = ['if headway_time<=2.0 and RSpeed<=0 and vLead!=0:', 'if headway_time<=2.0 and RSpeed>0 and vLead!=0:', 'if headway_time>2.0 and RSpeed>0 and vLead!=0:','if headway_time>2.0 and RSpeed<=0 and vLead!=0:']
	trigger_STPA_list = ['if frameIdx>1000 and (headway_time>2.0 and RSpeed<0 and Lead_vehicle_in_vision  or Lead_vehicle_in_vision==False):'] 

	gen_code_common_fixedduration(title,fileLoc,faultLoc,variable, newvalue,trigger_STPA_list=trigger_STPA_list,additional_code=additional_code)


def gen_max_steer_left(sceneNum):#S3
	title = str(sceneNum)+'_max_steer_left'
	fileLoc = 'tools/sim/bridge.py'
	faultLoc = '#throttle:HOOK#'
	variable = 'FI_flag'
	newvalue = '1'
	# newvalue2 = '4'
	additional_code='//FI_Type |= 0x04'

	trigger_STPA_list = ['if speed>15 and laneLineleft>-1.25:'] 

	gen_code_common_fixedduration(title,fileLoc,faultLoc,variable, newvalue,trigger_STPA_list=trigger_STPA_list,additional_code=additional_code)

def gen_max_steer_right(sceneNum):#S4
	title = str(sceneNum)+'_max_steer_right'
	fileLoc = 'tools/sim/bridge.py'
	faultLoc = '#throttle:HOOK#'
	variable = 'FI_flag'
	newvalue = '1'
	# newvalue2 = '4'
	additional_code='//FI_Type |= 0x08'

	trigger_STPA_list = ['if speed>15 and laneLineleft<1.25:'] 

	gen_code_common_fixedduration(title,fileLoc,faultLoc,variable, newvalue,trigger_STPA_list=trigger_STPA_list,additional_code=additional_code)

def gen_max_throttle_steer(sceneNum):#S5
	title = str(sceneNum)+'_max_throttle_steer'
	fileLoc = 'tools/sim/bridge.py'
	faultLoc = '#throttle:HOOK#'
	variable = 'FI_flag'
	newvalue = '1'
	# newvalue2 = '4'
	additional_code='//FI_Type |= 0x01'

	# trigger_code_list = ['if headway_time<=2.0 and RSpeed<=0 and vLead!=0:', 'if headway_time<=2.0 and RSpeed>0 and vLead!=0:', 'if headway_time>2.0 and RSpeed>0 and vLead!=0:','if headway_time>2.0 and RSpeed<=0 and vLead!=0:']
	trigger_STPA_list = ['if headway_time<=2.0 and RSpeed>0 and vLead!=0:']#, 'if headway_time<=2.0 and RSpeed<=0 and vLead!=0:']

	gen_code_common_fixedduration(title,fileLoc,faultLoc,variable, newvalue,trigger_STPA_list=trigger_STPA_list,additional_code=additional_code,FI_H3_combine_enable = True)

def gen_max_brake_steer(sceneNum):#S6
	title = str(sceneNum)+'_max_brake_steer'
	fileLoc = 'tools/sim/bridge.py'
	faultLoc = '#throttle:HOOK#'
	variable = 'FI_flag'
	newvalue = '1'
	# newvalue2 = '4'
	additional_code='//FI_Type |= 0x02'

	# trigger_code_list = ['if headway_time<=2.0 and RSpeed<=0 and vLead!=0:', 'if headway_time<=2.0 and RSpeed>0 and vLead!=0:', 'if headway_time>2.0 and RSpeed>0 and vLead!=0:','if headway_time>2.0 and RSpeed<=0 and vLead!=0:']
	trigger_STPA_list = ['if frameIdx>1000 and (headway_time>2.0 and RSpeed<0 and Lead_vehicle_in_vision  or Lead_vehicle_in_vision==False):'] 

	gen_code_common_fixedduration(title,fileLoc,faultLoc,variable, newvalue,trigger_STPA_list=trigger_STPA_list,additional_code=additional_code,FI_H3_combine_enable = True)

##########################################################################################
	
def gen_max_throttle_random_duration(sceneNum):#S11
	title = str(sceneNum)+'_max_throttle_random_duration'
	fileLoc = 'tools/sim/bridge.py'
	faultLoc = '#throttle:HOOK#'
	variable = 'FI_flag'
	newvalue = '1'
	# newvalue2 = '4'
	additional_code='//FI_Type |= 0x01'

	# trigger_code_list = ['if headway_time<=2.0 and RSpeed<=0 and vLead!=0:', 'if headway_time<=2.0 and RSpeed>0 and vLead!=0:', 'if headway_time>2.0 and RSpeed>0 and vLead!=0:','if headway_time>2.0 and RSpeed<=0 and vLead!=0:']
	trigger_STPA_list = ['if headway_time<=2.0 and RSpeed>0 and vLead!=0:']#, 'if headway_time<=2.0 and RSpeed<=0 and vLead!=0:']

	gen_code_common_fixedduration(title,fileLoc,faultLoc,variable, newvalue,trigger_STPA_list=trigger_STPA_list,additional_code=additional_code,change_duraiton=True)

def gen_max_brake_random_duration(sceneNum):#S12

	title = str(sceneNum)+'_max_brake_random_duration'
	fileLoc = 'tools/sim/bridge.py'
	faultLoc = '#throttle:HOOK#'
	variable = 'FI_flag'
	newvalue = '1'
	# newvalue2 = '4'
	additional_code='//FI_Type |= 0x02'

	# trigger_code_list = ['if headway_time<=2.0 and RSpeed<=0 and vLead!=0:', 'if headway_time<=2.0 and RSpeed>0 and vLead!=0:', 'if headway_time>2.0 and RSpeed>0 and vLead!=0:','if headway_time>2.0 and RSpeed<=0 and vLead!=0:']
	trigger_STPA_list = ['if frameIdx>1000 and (headway_time>2.0 and RSpeed<0 and Lead_vehicle_in_vision  or Lead_vehicle_in_vision==False):'] 

	gen_code_common_fixedduration(title,fileLoc,faultLoc,variable, newvalue,trigger_STPA_list=trigger_STPA_list,additional_code=additional_code,change_duraiton=True)

def gen_max_steer_left_random_duration(sceneNum):#S13
	title = str(sceneNum)+'_max_steer_left_random_duration'
	fileLoc = 'tools/sim/bridge.py'
	faultLoc = '#throttle:HOOK#'
	variable = 'FI_flag'
	newvalue = '1'
	# newvalue2 = '4'
	additional_code='//FI_Type |= 0x04'

	trigger_STPA_list = ['if speed>15 and laneLineleft>-1.25:'] 

	gen_code_common_fixedduration(title,fileLoc,faultLoc,variable, newvalue,trigger_STPA_list=trigger_STPA_list,additional_code=additional_code,change_duraiton=True)

def gen_max_steer_right_random_duration(sceneNum):#S14
	title = str(sceneNum)+'_max_steer_right_random_duration'
	fileLoc = 'tools/sim/bridge.py'
	faultLoc = '#throttle:HOOK#'
	variable = 'FI_flag'
	newvalue = '1'
	# newvalue2 = '4'
	additional_code='//FI_Type |= 0x08'

	trigger_STPA_list = ['if speed>15 and laneLineleft<1.25:'] 

	gen_code_common_fixedduration(title,fileLoc,faultLoc,variable, newvalue,trigger_STPA_list=trigger_STPA_list,additional_code=additional_code,change_duraiton=True)


def gen_max_throttle_steer_random_duration(sceneNum):#S15
	title = str(sceneNum)+'_max_throttle_steer_random_duration'
	fileLoc = 'tools/sim/bridge.py'
	faultLoc = '#throttle:HOOK#'
	variable = 'FI_flag'
	newvalue = '1'
	# newvalue2 = '4'
	additional_code='//FI_Type |= 0x01'

	# trigger_code_list = ['if headway_time<=2.0 and RSpeed<=0 and vLead!=0:', 'if headway_time<=2.0 and RSpeed>0 and vLead!=0:', 'if headway_time>2.0 and RSpeed>0 and vLead!=0:','if headway_time>2.0 and RSpeed<=0 and vLead!=0:']
	trigger_STPA_list = ['if headway_time<=2.0 and RSpeed>0 and vLead!=0:']#, 'if headway_time<=2.0 and RSpeed<=0 and vLead!=0:']

	gen_code_common_fixedduration(title,fileLoc,faultLoc,variable, newvalue,trigger_STPA_list=trigger_STPA_list,additional_code=additional_code,change_duraiton=True,FI_H3_combine_enable = True)

def gen_max_brake_steer_random_duration(sceneNum):#S16
	title = str(sceneNum)+'_max_brake_steer_random_duration'
	fileLoc = 'tools/sim/bridge.py'
	faultLoc = '#throttle:HOOK#'
	variable = 'FI_flag'
	newvalue = '1'
	# newvalue2 = '4'
	additional_code='//FI_Type |= 0x02'

	# trigger_code_list = ['if headway_time<=2.0 and RSpeed<=0 and vLead!=0:', 'if headway_time<=2.0 and RSpeed>0 and vLead!=0:', 'if headway_time>2.0 and RSpeed>0 and vLead!=0:','if headway_time>2.0 and RSpeed<=0 and vLead!=0:']
	trigger_STPA_list = ['if frameIdx>1000 and (headway_time>2.0 and RSpeed<0 and Lead_vehicle_in_vision  or Lead_vehicle_in_vision==False):'] 

	gen_code_common_fixedduration(title,fileLoc,faultLoc,variable, newvalue,trigger_STPA_list=trigger_STPA_list,additional_code=additional_code,change_duraiton=True,FI_H3_combine_enable = True)

##########################################################################################
def gen_max_throttle_random_t0(sceneNum):#S21
	title = str(sceneNum)+'_max_throttle_random_t0'
	fileLoc = 'tools/sim/bridge.py'
	faultLoc = '#throttle:HOOK#'
	variable = 'FI_flag'
	newvalue = '1'
	# newvalue2 = '4'
	additional_code='//FI_Type |= 0x01'

	# trigger_code_list = ['if headway_time<=2.0 and RSpeed<=0 and vLead!=0:', 'if headway_time<=2.0 and RSpeed>0 and vLead!=0:', 'if headway_time>2.0 and RSpeed>0 and vLead!=0:','if headway_time>2.0 and RSpeed<=0 and vLead!=0:']
	trigger_STPA_list = ['if headway_time<=2.0 and RSpeed>0 and vLead!=0:']#, 'if headway_time<=2.0 and RSpeed<=0 and vLead!=0:']

	gen_code_common_fixedduration(title,fileLoc,faultLoc,variable, newvalue,trigger_STPA_list=trigger_STPA_list,additional_code=additional_code,change_duraitont0=True)

def gen_max_brake_random_t0(sceneNum):#S22
	title = str(sceneNum)+'_max_brake_random_t0'
	fileLoc = 'tools/sim/bridge.py'
	faultLoc = '#throttle:HOOK#'
	variable = 'FI_flag'
	newvalue = '1'
	# newvalue2 = '4'
	additional_code='//FI_Type |= 0x02'

	# trigger_code_list = ['if headway_time<=2.0 and RSpeed<=0 and vLead!=0:', 'if headway_time<=2.0 and RSpeed>0 and vLead!=0:', 'if headway_time>2.0 and RSpeed>0 and vLead!=0:','if headway_time>2.0 and RSpeed<=0 and vLead!=0:']
	trigger_STPA_list = ['if frameIdx>1000 and (headway_time>2.0 and RSpeed<0 and Lead_vehicle_in_vision  or Lead_vehicle_in_vision==False):'] 

	gen_code_common_fixedduration(title,fileLoc,faultLoc,variable, newvalue,trigger_STPA_list=trigger_STPA_list,additional_code=additional_code,change_duraitont0=True)

def gen_max_steer_left_random_t0(sceneNum):#S23
	title = str(sceneNum)+'_max_steer_left_random_t0'
	fileLoc = 'tools/sim/bridge.py'
	faultLoc = '#throttle:HOOK#'
	variable = 'FI_flag'
	newvalue = '1'
	# newvalue2 = '4'
	additional_code='//FI_Type |= 0x04'

	trigger_STPA_list = ['if speed>15 and laneLineleft>-1.25:'] 

	gen_code_common_fixedduration(title,fileLoc,faultLoc,variable, newvalue,trigger_STPA_list=trigger_STPA_list,additional_code=additional_code,change_duraitont0=True)


def gen_max_steer_right_random_t0(sceneNum):#S24
	title = str(sceneNum)+'_max_steer_right_random_t0'
	fileLoc = 'tools/sim/bridge.py'
	faultLoc = '#throttle:HOOK#'
	variable = 'FI_flag'
	newvalue = '1'
	# newvalue2 = '4'
	additional_code='//FI_Type |= 0x08'

	trigger_STPA_list = ['if speed>15 and laneLineleft<1.25:'] 

	gen_code_common_fixedduration(title,fileLoc,faultLoc,variable, newvalue,trigger_STPA_list=trigger_STPA_list,additional_code=additional_code,change_duraitont0=True)


def gen_max_throttle_steer_random_t0(sceneNum):#S25
	title = str(sceneNum)+'_max_throttle_steer_random_t0'
	fileLoc = 'tools/sim/bridge.py'
	faultLoc = '#throttle:HOOK#'
	variable = 'FI_flag'
	newvalue = '1'
	# newvalue2 = '4'
	additional_code='//FI_Type |= 0x01'

	# trigger_code_list = ['if headway_time<=2.0 and RSpeed<=0 and vLead!=0:', 'if headway_time<=2.0 and RSpeed>0 and vLead!=0:', 'if headway_time>2.0 and RSpeed>0 and vLead!=0:','if headway_time>2.0 and RSpeed<=0 and vLead!=0:']
	trigger_STPA_list = ['if headway_time<=2.0 and RSpeed>0 and vLead!=0:']#, 'if headway_time<=2.0 and RSpeed<=0 and vLead!=0:']

	gen_code_common_fixedduration(title,fileLoc,faultLoc,variable, newvalue,trigger_STPA_list=trigger_STPA_list,additional_code=additional_code,change_duraitont0=True,FI_H3_combine_enable = True)

def gen_max_brake_steer_random_t0(sceneNum):#S26
	title = str(sceneNum)+'_max_brake_steer_random_t0'
	fileLoc = 'tools/sim/bridge.py'
	faultLoc = '#throttle:HOOK#'
	variable = 'FI_flag'
	newvalue = '1'
	# newvalue2 = '4'
	additional_code='//FI_Type |= 0x02'

	# trigger_code_list = ['if headway_time<=2.0 and RSpeed<=0 and vLead!=0:', 'if headway_time<=2.0 and RSpeed>0 and vLead!=0:', 'if headway_time>2.0 and RSpeed>0 and vLead!=0:','if headway_time>2.0 and RSpeed<=0 and vLead!=0:']
	trigger_STPA_list = ['if frameIdx>1000 and (headway_time>2.0 and RSpeed<0 and Lead_vehicle_in_vision  or Lead_vehicle_in_vision==False):'] 

	gen_code_common_fixedduration(title,fileLoc,faultLoc,variable, newvalue,trigger_STPA_list=trigger_STPA_list,additional_code=additional_code,change_duraitont0=True,FI_H3_combine_enable = True)

def gen_model_corruption(sceneNum):#S31
	title = str(sceneNum)+'_model_corruption'
	fileLoc = 'tools/sim/bridge.py'
	faultLoc = '#throttle:HOOK#'
	variable = 'FI_flag'
	newvalue = '1'
	# newvalue2 = '4'
	additional_code='//FI_Type |= 0x10'

	# trigger_code_list = ['if headway_time<=2.0 and RSpeed<=0 and vLead!=0:', 'if headway_time<=2.0 and RSpeed>0 and vLead!=0:', 'if headway_time>2.0 and RSpeed>0 and vLead!=0:','if headway_time>2.0 and RSpeed<=0 and vLead!=0:']
	trigger_STPA_list = ['if headway_time<=2.0 and RSpeed>0 and vLead!=0:']#, 'if headway_time<=2.0 and RSpeed<=0 and vLead!=0:']

	gen_code_common_fixedduration(title,fileLoc,faultLoc,variable, newvalue,trigger_STPA_list=trigger_STPA_list,additional_code=additional_code,RepeatTimes=50)


####################################################

###_main_###

with open('run_fault_inject_monitor_V2_campaign.sh', 'w') as runFile:
	runFile.write('#Usage: python3 run.py fault_library_monitor_V2\n')

with open('run_fault_inject_monitor_V2_STPA_campaign.sh', 'w') as runFile:
    runFile.write('#Usage: python3 run.py  fault_library_monitor_V2_STPA\n')
	
scenarios = {
1 : gen_max_throttle, #STPA, and random t0&fixed duration
2 : gen_max_brake,
3 : gen_max_steer_left,
4 : gen_max_steer_right,
5 : gen_max_throttle_steer,
6 : gen_max_brake_steer,
11 : gen_max_throttle_random_duration, #STPA
12 : gen_max_brake_random_duration,
13 : gen_max_steer_left_random_duration,
14 : gen_max_steer_right_random_duration,
15 : gen_max_throttle_steer_random_duration,
16 : gen_max_brake_steer_random_duration,
21 : gen_max_throttle_random_t0, #random t0 and random duration
22 : gen_max_brake_random_t0,
23 : gen_max_steer_left_random_t0,
24 : gen_max_steer_right_random_t0,
25 : gen_max_throttle_steer_random_t0,
26 : gen_max_brake_steer_random_t0,
31 : gen_model_corruption,
}

random.seed(3) 
for sceneNum in [31]:#1,2,3,4,5,6,11,12,13,14,15,16,21,22,23,24,25,26]:
	scenarios[sceneNum](sceneNum)

