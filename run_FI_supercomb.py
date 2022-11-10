import os
import os.path
import time
from sys import argv
import numpy as np

def find_files(path):
    fileset= []
    for root, dirs, files in os.walk(path):
        for file in files:
            if file.endswith(".onnx"):
                fileresult = os.path.join(root, file)
                fileset.append(fileresult)
    return fileset

def rename_modelist(modellsit):
    modellsit = np.load("./supercombmodellist.npy")
    newmodellist = []
    # print(modellsit)
    for i in range(len(modellsit)):
        file = modellsit[i]
        newfile = file.split('/')
        newfile[-1] = f"{i+1}_"+newfile[-1]
        newfile = '/'.join(newfile)
        # cmdstr = 'mv '+file+' '+newfile
        # print(cmdstr)
        # os.system(cmdstr)
        newmodellist.append(newfile)
    # print(newmodellist)
    # np.save("./supercombmodellist_new.npy",newmodellist)

if __name__ == "__main__":   
    if os.path.isfile("./supercombmodellist_new.npy") != True:
        path = "../supercomb_models/models"
        if os.path.isdir(path):
            filelist = find_files(path)
            print(filelist,len(filelist))
            # np.save("./supercombmodellist.npy",filelist)
        else:
            print("path error!")
    else:
        modellsit = np.load("./supercombmodellist_new.npy")
        for model in modellsit[:10]:

            print(f"=============Processing model {model}============")
            #step 1: update the model with the corrupted model
            cmdstr=f"cp {model} ./models/supercombo.onnx"
            print(cmdstr)
            os.system(cmdstr)

            #step2: run the simulation
            cmdstr="./run_fault_inject_monitor_V2_campaign_supercomb.sh"
            os.system(cmdstr)

            #wait 
            while(True):
                fp = open("./selfdrive/manager/process_status.txt",'r')
                line = fp.readlines()
                if line[0][0] =="2":
                    print("Done!")
                    fp.close()

                    fp = open("./selfdrive/manager/process_status.txt",'w')
                    fp.write("0")
                    print("Reset process status and exit!")
                    fp.close()

                    time.sleep(5)
                    break
                
                time.sleep(1)

            #step 3: move result files
            if os.path.isdir("../output_files/31_model_corruption"):
                modelname = model.split('/')[-1].split('.')[0]
                cmdstr=f"mv ../output_files/31_model_corruption ../output_files/{modelname}_scenario31_model_corruption"
                print(cmdstr)
                os.system(cmdstr)





    