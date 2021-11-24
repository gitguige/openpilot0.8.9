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
def gen_code_common_fixedduration(title,fileLoc,faultLoc,variable,newvalue,newvalue2=0,early_start=False,trigger_STPA_list=['if xxxxx:'],additional_code=''):
		
	trigger = 'frameIdx' #trigger_random
	code = []
	code_STPA=[]
	#param = []
	# N_duration =4
	per_time_range = 1
	time_partition = np.arange(5,45,per_time_range) 
	valuelist = []
	valuelist.append(newvalue)
	if newvalue2:
		valuelist.append(newvalue2)

	# additional_code='//brake_out=0//FI_flage=1'
	# additional_code='//FI_flage=1'

	for valueitem in valuelist:
		#random FI
		for tindex in range(len(time_partition)): #10
			trigger_time = random.randint(time_partition[tindex],time_partition[tindex]+per_time_range-1) #t
			stop_time = trigger_time + 2.5 # 2.5s
			code.append(gen_stuck_code('',trigger, trigger_time*100,stop_time*100, variable, valueitem,additional_code=additional_code))

		#STPA FI
		for trigger_STPA in trigger_STPA_list:
			for round in range(20): #repeat for xx times
				code_STPA.append(gen_stuck_code(trigger_STPA,trigger, trigger_time*100,stop_time*100, variable, valueitem,additional_code=additional_code))

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


def gen_max_throttle(sceneNum):#S1
	title = str(sceneNum)+'_max_throttle'
	fileLoc = 'tools/sim/bridge.py'
	faultLoc = '#throttle:HOOK#'
	variable = 'throttle_out'
	newvalue = '0.6'
	# newvalue2 = '4'
	additional_code='//brake_out=0//FI_flage=1'

	# trigger_code_list = ['if headway_time<=2.0 and RSpeed<=0 and vLead!=0:', 'if headway_time<=2.0 and RSpeed>0 and vLead!=0:', 'if headway_time>2.0 and RSpeed>0 and vLead!=0:','if headway_time>2.0 and RSpeed<=0 and vLead!=0:']
	trigger_STPA_list = ['if headway_time<=2.0 and RSpeed>0 and vLead!=0:']#, 'if headway_time<=2.0 and RSpeed<=0 and vLead!=0:']

	gen_code_common_fixedduration(title,fileLoc,faultLoc,variable, newvalue,trigger_STPA_list=trigger_STPA_list,additional_code=additional_code)

def gen_max_brake(sceneNum):#S1
	title = str(sceneNum)+'_max_brake'
	fileLoc = 'tools/sim/bridge.py'
	faultLoc = '#throttle:HOOK#'
	variable = 'brake_out'
	newvalue = '1'
	# newvalue2 = '4'
	additional_code='//throttle_out=0//FI_flage=1'

	# trigger_code_list = ['if headway_time<=2.0 and RSpeed<=0 and vLead!=0:', 'if headway_time<=2.0 and RSpeed>0 and vLead!=0:', 'if headway_time>2.0 and RSpeed>0 and vLead!=0:','if headway_time>2.0 and RSpeed<=0 and vLead!=0:']
	trigger_STPA_list = ['if headway_time>2.0 and RSpeed<=0 and vLead!=0:'] 

	gen_code_common_fixedduration(title,fileLoc,faultLoc,variable, newvalue,trigger_STPA_list=trigger_STPA_list,additional_code=additional_code)

def gen_min_dRel(sceneNum):#S20
	title = str(sceneNum)+'_minimize_dRel'

	variable = 'radar_dRel'

	fileLoc = 'selfdrive/test/plant/plant.py'
	faultLoc = '#radar_dRel:HOOK#'
	newvalue = '10'
	# newvalue2 = '4'

	gen_code_common_fixedduration(title,fileLoc,faultLoc,variable, newvalue,early_start=True)



##########################################################################################

###_main_###

with open('run_fault_inject_monitor_V2_campaign.sh', 'w') as runFile:
	runFile.write('#Usage: python3 run.py fault_library_monitor_V2\n')

with open('run_fault_inject_monitor_V2_STPA_campaign.sh', 'w') as runFile:
    runFile.write('#Usage: python3 run.py  fault_library_monitor_V2_STPA\n')
	
scenarios = {
1 : gen_max_throttle,
2 : gen_max_brake,
# 3 : gen_aboveTarget_nodec_sub_dRel,
# 4 : gen_aboveTarget_nodec_stuck_dRel,
# 5 : gen_belowTarget_add_vRel,
# 6 : gen_belowTarget_stuck_vRel,
# 7 : gen_aboveTarget_sub_vRel,
# 8 : gen_aboveTarget_stuck_vRel,


}

random.seed(3) 
for sceneNum in [1]:
	scenarios[sceneNum](sceneNum)

