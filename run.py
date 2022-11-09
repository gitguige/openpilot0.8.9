import os
import os.path
import numpy as np
import time
from sys import argv


def insert_fault_code(fileLoc, faultLoc, codeline):
    brk = 0
    bkupFile = fileLoc+'.bkup'
    if os.path.isfile(bkupFile) != True:
      cmd = 'cp ' + fileLoc + ' ' + bkupFile
      os.system(cmd)
    else:
      print ('Bkup file already exists!!')

    src_fp = open(fileLoc, 'w')
    bkup_fp = open(bkupFile, 'r')

    for line in bkup_fp:
      src_fp.write(line)
      if brk>0:
        for i in range(1, leadSp+1):
          src_fp.write(' ')
        src_fp.write('else:'+'\n')
        for l in np.arange(brk,len(codeline)):
            for i in range(1, leadSp+3):
              src_fp.write(' ')
            src_fp.write(codeline[l]+'\n')

      brk = 0

      if faultLoc in line:
        leadSp = len(line) - len(line.lstrip(' ')) # calculate the leading spaces

        for i in range(1, leadSp+1):
          src_fp.write(' ')
        src_fp.write(codeline[0]+'\n')

        for l in np.arange(1,len(codeline)):
          if codeline[l] != 'none\n':
            for i in range(1, leadSp+3):
              src_fp.write(' ')
            src_fp.write(codeline[l]+'\n')
          else:
            brk=l+1
            for i in range(1,3):
              src_fp.write(' ')
            break

    src_fp.close()
    bkup_fp.close()



#fileName: fault_library_monitor_V2/scenario_1
def inject_fault(fileName):
    in_file = fileName+'.txt'
    # outfile_path = 'selfdrive/test/tests/plant/out/longitudinal/'
    sceneLine  = fileName.split('_')
    sceneNum = sceneLine[len(sceneLine)-1]

    # recFaultTime="//fltTime=open(\'out/longitudinal/fault_times.txt\',\'a+\')//fltTime.write(str(sec_since_boot())+\'||\')//fltTime.close()"

    with open(in_file, 'r') as fp:
        print (in_file)
        line = fp.readline() # title:1_max_throttle
        title = line.split(':')
        title = title[1].replace('\n','') #1_max_throttle
        scenario_num = title.split('_')[0] #1

        if os.path.isdir('../output_files/'+title) != True:
          os.makedirs('../output_files/'+title)


        summFile = open('../output_files/'+title+'/summary.csv','w')
        summLine = 'Scenario#,Fault#,Fault-line,vLead,InitDist,vLead2,Alerts,Hazards,T1,T2,T3,Alert_flag,Hazard_flag,Fault_duration,Num_laneInvasion\n'
        summFile.write(summLine)
        summFile.close()

        line = fp.readline() # fault location line
        lineSeg = line.split('//') #location//tools/sim/bridge.py//#throttle:HOOK#
        fileLoc = lineSeg[1]
        faultLoc = lineSeg[2]

        for line in fp:
          lineSeg = line.split('//') #fault 1//if frameIdx>=500 and frameIdx<750.0://throttle_out=0.6
          startWord = lineSeg[0].split(' ')
          faultNum = startWord[1]
          del lineSeg[0]

          if startWord[0]=='fault':
            print ("+++++++++++"+title+"++++++++++++++"+faultNum+"++++++++++++++")
            output_dir = '../output_files/'+title+'/'+faultNum
            if os.path.isdir(output_dir) != True:
              os.makedirs(output_dir)

              insert_fault_code(fileLoc, faultLoc, lineSeg)

              for InitDist in [50]:#,70,100]:
                for vLead in [100]:#,200]:#20,100]:
                  for vLead2 in [100]:#,200]:

                    for reInitialize_bridge_loop in range(3): #rerun 3 times at most if bridge fails to start correctly
                      os.system('./run_bridge.sh {} {} {}'.format(vLead,InitDist,vLead2)) # run the openpilot simulator outside docker

                      fp_temp = open("tools/sim/temp.txt",'r')
                      tempLine = fp_temp.readline()
                      tempLine = tempLine.replace('\n','')

                      if "buttonEnable" in tempLine: # skip if bridge is initialized correctly
                        break                   
                    
                    summFile = open('../output_files/'+title+'/summary.csv','a')
                    faultLine = '||'.join(lineSeg)
                    faultLine = faultLine.replace('\n','')
                    summLine = '%d,%d,"%s",%d,%d,%d,' %(int(scenario_num),int(faultNum),faultLine,vLead,InitDist,vLead2)               
                    summFile.write(summLine+tempLine+'\n')
                    summFile.close()
                    fp_temp.close()

              # '''Copy all output files in a common directory'''
              # cmd = 'cp -a ' + outfile_path+'/.' + ' ' + output_dir
              # os.system(cmd)
              cmd = 'mv tools/sim/results/*  ../output_files/{}/{}/'.format(title,faultNum)
              os.system(cmd)

        #========update process status===========
        fp = open("./selfdrive/manager/process_status.txt",'w')
        fp.write("1") #1; finished
        print("Set process status and exit!")
        fp.close()
        #=========================================
       
        print ('Fault injection and execution done !!!')
        bkupFile = fileLoc+'.bkup'
        refFile = fileLoc+'.reference'       
        cmd = 'cp ' + fileLoc + ' ' + refFile
        os.system(cmd)
        cmd = 'cp ' + bkupFile + ' ' + fileLoc
        os.system(cmd)
        cmd = 'rm ' + bkupFile
        os.system(cmd)
        print ('Original file restored')
    cmd = 'cp '+in_file + ' ' +'../output_files/'+title
    os.system(cmd)

start = time.time()

if len(argv)>1:
  inject_fault(argv[1])
else:
  print ('Fault library filename is missing, pass the filename as argument')

print ('\n\n Total runtime: %f seconds' % (time.time()-start))

