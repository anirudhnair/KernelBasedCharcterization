'''
Created on Dec 28, 2013

@author: Anirudh Jayakumar
         jayakumar.anirudh@gmail.com 
'''
import pandas as pd
import numpy as np
import gc
import os, re
from dtw import dtw
from prettytable import PrettyTable
from EBSTraceStat import EBSTraceStat
from TAUTraceStat import TAUTraceStat
from Settings import Common
from ObjDumpReader import ObjDumpReader

                
def AnalyzeFromTrace(dirPath,funcName,startIndex,endIndex):
    import glob
    filePattern = dirPath + '/ebstrace.raw*'    
    listFiles = glob.glob(filePattern)
    pids = []
    for file_ in listFiles:
        if (re.search('~', file_) or re.search('bak',file_)):
            None
        else:
            pid = int(os.path.basename(file_).split(".")[2])
            pids.append(pid)
    
    pids.sort()
    pidMap = {}
    index = 0
    for pid in pids:
        pidMap[pid] = index
        index+=1
    gc.collect()
    objDump = ObjDumpReader.ObjDumpReader(dirPath + '/objdump')
    objDump.CleanTrace()
    objDump.LoadTrace()
    
    
    tauTrace = TAUTraceStat.TAUTraceStat(dirPath + '/dump')
    tauTrace.CleanTrace()
    tauTrace.LoadTrace()
    pid_papiiterSaxMap = {}
    pid_iterIPFDMap = {}
    for file_ in listFiles:
        if (re.search('~', file_) or re.search('bak',file_)):
            None
        else:
            #print file_
            pid = int(os.path.basename(file_).split(".")[2])
            funcEntryExitList = tauTrace.GetListofFunctionEntryExitPoints(funcName, pidMap[pid])
        
            startTimes = []
            endTimes   = []
            for item in funcEntryExitList[startIndex:endIndex+1]:
                startTimes.append(item[0])
                endTimes.append(item[1])
            gc.collect()   
            ebsTrace = EBSTraceStat.EBSTraceStat(file_)
            ebsTrace.CleanTrace()
            ebsTrace.LoadTrace()
            ebsTrace.RegisterObjDumpReader(objDump)
            metricList = ebsTrace.GetMetricsList()
            sizeList = len(metricList)
            papi_iterSaxMap = {}
            for index in range(2,sizeList):
                iterSax = ebsTrace.AnalyzeBetweenTimeStamps(0, index, startTimes, endTimes)
                papi_iterSaxMap[metricList[index]] = iterSax
            
            iter_IPFDMap = ebsTrace.AnalyzeIPFDBetweenTimeStamps(startTimes, endTimes)
            pid_papiiterSaxMap[pidMap[ebsTrace.GetPID()]] = papi_iterSaxMap
            pid_iterIPFDMap[pidMap[ebsTrace.GetPID()]] = iter_IPFDMap
            gc.collect()
    return  pid_papiiterSaxMap, pid_iterIPFDMap      

def AnalyzeAcrossRuns(listOfLists, funList, startIter, endIter):           
    index_ = 0
    run_probSizepidpapiiterSaxMap = {}
    run_probSizepiditerIPFDMap = {}
    for group in listOfLists:
        probSize_pidpapiiterSaxMap = {}
        probSize_piditerIPFDMap = {}
        runName = os.path.basename(group[0]).split("_")[0]
        for run in group:
            sizeClass = os.path.basename(run).split("_")[1]
            funcName = funList[index_]
            pid_papiiterSaxMap, pid_iterIPFDMap = AnalyzeFromTrace(run,funcName,startIter, endIter)
            if sizeClass in probSize_pidpapiiterSaxMap:    
                pidMapOld = probSize_pidpapiiterSaxMap[sizeClass]
                for key, value in pid_papiiterSaxMap.iteritems():
                    pidMapOld[key].update(value)
            else:                        
                probSize_pidpapiiterSaxMap[sizeClass] = pid_papiiterSaxMap
            probSize_piditerIPFDMap[sizeClass] = pid_iterIPFDMap
        run_probSizepidpapiiterSaxMap[runName] = probSize_pidpapiiterSaxMap
        run_probSizepiditerIPFDMap[runName] = probSize_piditerIPFDMap
        index_+=1    
    return run_probSizepidpapiiterSaxMap, run_probSizepiditerIPFDMap
                    


def FormTableForPAPIAnalysis(result):
    #print result
    df = pd.DataFrame(columns=(Common.KERNEL, Common.CLASS, Common.PID,Common.PAPI,Common.ITER,Common.SAX))
    for run in result:
        runVal = result.get(run)
        #print "runval"
        #print runVal
        for size in runVal:
            sizeVal = runVal.get(size)
            for pid in sizeVal:
                pidVal = sizeVal.get(pid)
                for papi in pidVal:
                    papiVal = pidVal.get(papi)
                    for iter in papiVal:
                        iterVal = papiVal.get(iter)
                        row = pd.DataFrame([{Common.KERNEL:run, Common.CLASS:size, Common.PID:pid,Common.PAPI:papi.strip(),Common.ITER:iter,Common.SAX:iterVal}, ])
                        df = df.append(row, ignore_index=True)
                        print run + " " + size + " " + str(pid) + " " + papi.strip() + " " + str(iter) + " " + iterVal
    return df

def FormTableForIPFDAnalysis(result):
   
    df = pd.DataFrame(columns=(Common.KERNEL, Common.CLASS, Common.PID,Common.ITER,Common.IPFD))
    for run in result:
        runVal = result.get(run)
        for size in runVal:
            sizeVal = runVal.get(size)
            for pid in sizeVal:
                pidVal = sizeVal.get(pid)
                for iter in pidVal:
                    iterVal = pidVal.get(iter)
                    row = pd.DataFrame([{Common.KERNEL:run, Common.CLASS:size, Common.PID:pid,Common.ITER:iter,Common.IPFD:iterVal}, ])
                    df = df.append(row, ignore_index=True)
                    #print run + " " + size + " " + str(pid) + " " + + str(iter) + " " + iterVal
    return df



def IPFDAnalysisAcrossKernels():
    result, ipfd = AnalyzeAcrossRuns([['/home/anirudhj/WORK-IISC/AppCharacterization/TAUAnalysis/TAUTrace/BT_1', \
                                 '/home/anirudhj/WORK-IISC/AppCharacterization/TAUAnalysis/TAUTrace/BT_2', \
                                 '/home/anirudhj/WORK-IISC/AppCharacterization/TAUAnalysis/TAUTrace/BT_3'], \
                                ['/home/anirudhj/WORK-IISC/AppCharacterization/TAUAnalysis/TAUTrace/IS_1', \
                                 '/home/anirudhj/WORK-IISC/AppCharacterization/TAUAnalysis/TAUTrace/IS_2', \
                                 '/home/anirudhj/WORK-IISC/AppCharacterization/TAUAnalysis/TAUTrace/IS_3'], \
                                ['/home/anirudhj/WORK-IISC/AppCharacterization/TAUAnalysis/TAUTrace/MM_1', \
                                 '/home/anirudhj/WORK-IISC/AppCharacterization/TAUAnalysis/TAUTrace/MM_2', \
                                 '/home/anirudhj/WORK-IISC/AppCharacterization/TAUAnalysis/TAUTrace/MM_3'], 
                                ['/home/anirudhj/WORK-IISC/AppCharacterization/TAUAnalysis/TAUTrace/LU_1', \
                                 '/home/anirudhj/WORK-IISC/AppCharacterization/TAUAnalysis/TAUTrace/LU_2', \
                                 '/home/anirudhj/WORK-IISC/AppCharacterization/TAUAnalysis/TAUTrace/LU_3'], \
                                ['/home/anirudhj/WORK-IISC/AppCharacterization/TAUAnalysis/TAUTrace/NLU_1', \
                                 '/home/anirudhj/WORK-IISC/AppCharacterization/TAUAnalysis/TAUTrace/NLU_2', \
                                 '/home/anirudhj/WORK-IISC/AppCharacterization/TAUAnalysis/TAUTrace/NLU_3'], \
                                ['/home/anirudhj/WORK-IISC/AppCharacterization/TAUAnalysis/TAUTrace/SP_1', \
                                 '/home/anirudhj/WORK-IISC/AppCharacterization/TAUAnalysis/TAUTrace/SP_2', \
                                 '/home/anirudhj/WORK-IISC/AppCharacterization/TAUAnalysis/TAUTrace/SP_3'],
                                ['/home/anirudhj/WORK-IISC/AppCharacterization/TAUAnalysis/TAUTrace/TRANS_1', \
                                 '/home/anirudhj/WORK-IISC/AppCharacterization/TAUAnalysis/TAUTrace/TRANS_2', \
                                 '/home/anirudhj/WORK-IISC/AppCharacterization/TAUAnalysis/TAUTrace/TRANS_3'], \
                                ['/home/anirudhj/WORK-IISC/AppCharacterization/TAUAnalysis/TAUTrace/TRD_1', \
                                 '/home/anirudhj/WORK-IISC/AppCharacterization/TAUAnalysis/TAUTrace/TRD_2', \
                                 '/home/anirudhj/WORK-IISC/AppCharacterization/TAUAnalysis/TAUTrace/TRD_3'], \
                                ['/home/anirudhj/WORK-IISC/AppCharacterization/TAUAnalysis/TAUTrace/QR1_1', \
                                 '/home/anirudhj/WORK-IISC/AppCharacterization/TAUAnalysis/TAUTrace/QR1_2', \
                                 '/home/anirudhj/WORK-IISC/AppCharacterization/TAUAnalysis/TAUTrace/QR1_3'],
                                ['/home/anirudhj/WORK-IISC/AppCharacterization/TAUAnalysis/TAUTrace/QR2_1', \
                                 '/home/anirudhj/WORK-IISC/AppCharacterization/TAUAnalysis/TAUTrace/QR2_2', \
                                 '/home/anirudhj/WORK-IISC/AppCharacterization/TAUAnalysis/TAUTrace/QR2_3']] \
                                 ,['ADI','rank','PDSUMCHK','PBDGEMM','SSOR','ADI','PDMATGEN','PDTRDDRIVER','PDGEQRF','PDGEQRRV'],1,5)
    df = FormTableForIPFDAnalysis(ipfd)
    kernels = np.unique(df[Common.KERNEL])
    iters   = np.unique(df[Common.ITER])
    ranks   = np.unique(df[Common.PID])
    sizes   = np.unique(df[Common.CLASS])
    
    # intra size - intra rank
    print "Across iterations"
    x = PrettyTable([ "kernel" ,"max", "min", "mean","std"])
    x.align["kernel"] = "l"
    x.padding_width = 1 
    for kernel in kernels:               
        dist = []
        for size in sizes:
            for rank in ranks:
                ipfdList = df[(df[Common.KERNEL] == kernel) & (df[Common.CLASS] == size) \
                             & (df[Common.PID] == rank) ][Common.IPFD].values
                dist.extend(Common.EnumerateIPDFDistance(ipfdList,ipfdList,True))
        dist = np.array(dist)
        if( len(dist) > 0):
            x.add_row([kernel,np.amax(dist), np.amin(dist), np.mean(dist),np.std(dist)])
    print x
        
    # intra size - inter rank
    print "Across Ranks"
    x = PrettyTable([ "kernel" ,"max", "min", "mean","std"])
    x.align["kernel"] = "l"
    x.padding_width = 1 
    for kernel in kernels:
        dist = []
        for size in sizes:
            listIPDFList = []
            for rank in ranks:
                ipfdList = df[(df[Common.KERNEL] == kernel) & (df[Common.CLASS] == size) \
                              & (df[Common.PID] == rank) ][Common.IPFD].values
                listIPDFList.append(ipfdList)
            for i in range(len(listIPDFList)):
                for j in range(i+1,len(listIPDFList)):
                    dist.extend(Common.EnumerateIPDFDistance(listIPDFList[i],listIPDFList[j]))
                        
        dist = np.array(dist)            
        x.add_row([kernel,np.amax(dist), np.amin(dist), np.mean(dist),np.std(dist)])
    print x.get_string(sortby="mean")
    
    
    # inter size - inter rank
    print "Across problem sizes"
    x = PrettyTable([ "kernel" ,"max", "min", "mean","std"])
    x.align["kernel"] = "l"
    x.padding_width = 1 
    for kernel in kernels:
        dist = []
        listIPDFList = []
        for size in sizes:
            ipfdList = df[(df[Common.KERNEL] == kernel) & (df[Common.CLASS] == size) ][Common.IPFD].values
            listIPDFList.append(ipfdList)
        for i in range(len(listIPDFList)):
            for j in range(i+1,len(listIPDFList)):
                dist.extend(Common.EnumerateIPDFDistance(listIPDFList[i],listIPDFList[j]))
                        
        dist = np.array(dist)            
        x.add_row([kernel,np.amax(dist), np.amin(dist), np.mean(dist),np.std(dist)])
    print x.get_string(sortby="mean")
    
    print "Across kernels"
    x = PrettyTable(["max", "min", "mean","std"])
    x.align["kernel"] = "l"
    x.padding_width = 1     
    dist = []
        
    listIPDFList = []
    for kernel in kernels:
        ipfdList = df[(df[Common.KERNEL] == kernel)][Common.IPFD].values
        listIPDFList.append(ipfdList)
    for i in range(len(listIPDFList)):
        for j in range(i+1,len(listIPDFList)):
            dist.extend(Common.EnumerateIPDFDistance(listIPDFList[i],listIPDFList[j]))
                        
    dist = np.array(dist)            
    x.add_row([np.amax(dist), np.amin(dist), np.mean(dist),np.std(dist)])
    
    print x.get_string(sortby="mean")

def PAPIAnalysisAcrossKernels():
    result, ipfd = AnalyzeAcrossRuns([['/home/anirudhj/WORK-IISC/AppCharacterization/TAUAnalysis/TAUTrace/BT_1', \
                                 '/home/anirudhj/WORK-IISC/AppCharacterization/TAUAnalysis/TAUTrace/BT_2', \
                                 '/home/anirudhj/WORK-IISC/AppCharacterization/TAUAnalysis/TAUTrace/BT_3'], \
                                ['/home/anirudhj/WORK-IISC/AppCharacterization/TAUAnalysis/TAUTrace/IS_1', \
                                 '/home/anirudhj/WORK-IISC/AppCharacterization/TAUAnalysis/TAUTrace/IS_2', \
                                 '/home/anirudhj/WORK-IISC/AppCharacterization/TAUAnalysis/TAUTrace/IS_3'], \
                                ['/home/anirudhj/WORK-IISC/AppCharacterization/TAUAnalysis/TAUTrace/MM_1', \
                                 '/home/anirudhj/WORK-IISC/AppCharacterization/TAUAnalysis/TAUTrace/MM_2', \
                                 '/home/anirudhj/WORK-IISC/AppCharacterization/TAUAnalysis/TAUTrace/MM_3'], 
                                ['/home/anirudhj/WORK-IISC/AppCharacterization/TAUAnalysis/TAUTrace/LU_1', \
                                 '/home/anirudhj/WORK-IISC/AppCharacterization/TAUAnalysis/TAUTrace/LU_2', \
                                 '/home/anirudhj/WORK-IISC/AppCharacterization/TAUAnalysis/TAUTrace/LU_3'], \
                                ['/home/anirudhj/WORK-IISC/AppCharacterization/TAUAnalysis/TAUTrace/NLU_1', \
                                 '/home/anirudhj/WORK-IISC/AppCharacterization/TAUAnalysis/TAUTrace/NLU_2', \
                                 '/home/anirudhj/WORK-IISC/AppCharacterization/TAUAnalysis/TAUTrace/NLU_3'], \
                                ['/home/anirudhj/WORK-IISC/AppCharacterization/TAUAnalysis/TAUTrace/SP_1', \
                                 '/home/anirudhj/WORK-IISC/AppCharacterization/TAUAnalysis/TAUTrace/SP_2', \
                                 '/home/anirudhj/WORK-IISC/AppCharacterization/TAUAnalysis/TAUTrace/SP_3'],
                                ['/home/anirudhj/WORK-IISC/AppCharacterization/TAUAnalysis/TAUTrace/TRANS_1', \
                                 '/home/anirudhj/WORK-IISC/AppCharacterization/TAUAnalysis/TAUTrace/TRANS_2', \
                                 '/home/anirudhj/WORK-IISC/AppCharacterization/TAUAnalysis/TAUTrace/TRANS_3'], \
                                ['/home/anirudhj/WORK-IISC/AppCharacterization/TAUAnalysis/TAUTrace/TRD_1', \
                                 '/home/anirudhj/WORK-IISC/AppCharacterization/TAUAnalysis/TAUTrace/TRD_2', \
                                 '/home/anirudhj/WORK-IISC/AppCharacterization/TAUAnalysis/TAUTrace/TRD_3'], \
                                ['/home/anirudhj/WORK-IISC/AppCharacterization/TAUAnalysis/TAUTrace/QR_1', \
                                 '/home/anirudhj/WORK-IISC/AppCharacterization/TAUAnalysis/TAUTrace/QR_2', \
                                 '/home/anirudhj/WORK-IISC/AppCharacterization/TAUAnalysis/TAUTrace/QR_3'],
                                ['/home/anirudhj/WORK-IISC/AppCharacterization/TAUAnalysis/TAUTrace/QR_1', \
                                 '/home/anirudhj/WORK-IISC/AppCharacterization/TAUAnalysis/TAUTrace/QR_2', \
                                 '/home/anirudhj/WORK-IISC/AppCharacterization/TAUAnalysis/TAUTrace/QR_3'],
                                ['/home/anirudhj/WORK-IISC/AppCharacterization/TAUAnalysis/TAUTrace/QR_1', \
                                 '/home/anirudhj/WORK-IISC/AppCharacterization/TAUAnalysis/TAUTrace/QR_2', \
                                 '/home/anirudhj/WORK-IISC/AppCharacterization/TAUAnalysis/TAUTrace/QR_3'],
                                ['/home/anirudhj/WORK-IISC/AppCharacterization/TAUAnalysis/TAUTrace/QR_1', \
                                 '/home/anirudhj/WORK-IISC/AppCharacterization/TAUAnalysis/TAUTrace/QR_2', \
                                 '/home/anirudhj/WORK-IISC/AppCharacterization/TAUAnalysis/TAUTrace/QR_3'],
                                ['/home/anirudhj/WORK-IISC/AppCharacterization/TAUAnalysis/TAUTrace/QR_1', \
                                 '/home/anirudhj/WORK-IISC/AppCharacterization/TAUAnalysis/TAUTrace/QR_2', \
                                 '/home/anirudhj/WORK-IISC/AppCharacterization/TAUAnalysis/TAUTrace/QR_3'],
                                ['/home/anirudhj/WORK-IISC/AppCharacterization/TAUAnalysis/TAUTrace/QR_1', \
                                 '/home/anirudhj/WORK-IISC/AppCharacterization/TAUAnalysis/TAUTrace/QR_2', \
                                 '/home/anirudhj/WORK-IISC/AppCharacterization/TAUAnalysis/TAUTrace/QR_3'],
                                ['/home/anirudhj/WORK-IISC/AppCharacterization/TAUAnalysis/TAUTrace/QR_1', \
                                 '/home/anirudhj/WORK-IISC/AppCharacterization/TAUAnalysis/TAUTrace/QR_2', \
                                 '/home/anirudhj/WORK-IISC/AppCharacterization/TAUAnalysis/TAUTrace/QR_3'],
                                ['/home/anirudhj/WORK-IISC/AppCharacterization/TAUAnalysis/TAUTrace/QR_1', \
                                 '/home/anirudhj/WORK-IISC/AppCharacterization/TAUAnalysis/TAUTrace/QR_2', \
                                 '/home/anirudhj/WORK-IISC/AppCharacterization/TAUAnalysis/TAUTrace/QR_3'],
                                ['/home/anirudhj/WORK-IISC/AppCharacterization/TAUAnalysis/TAUTrace/QR_1', \
                                 '/home/anirudhj/WORK-IISC/AppCharacterization/TAUAnalysis/TAUTrace/QR_2', \
                                 '/home/anirudhj/WORK-IISC/AppCharacterization/TAUAnalysis/TAUTrace/QR_3'],
                                ['/home/anirudhj/WORK-IISC/AppCharacterization/TAUAnalysis/TAUTrace/QR_1', \
                                 '/home/anirudhj/WORK-IISC/AppCharacterization/TAUAnalysis/TAUTrace/QR_2', \
                                 '/home/anirudhj/WORK-IISC/AppCharacterization/TAUAnalysis/TAUTrace/QR_3']] \
                                 ,['ADI','rank','DGEMM','PBDGEMM','SSOR','ADI','PDMATGEN','PDTRDDRIVER','PDGEQRF','PDGEQRRV' \
                                 , 'PDGEQLF','PDGEQLRV','PDGELQF','PDGELQRV','PDGERQF','PDGERQRV','PDGEQPF','PDGEQRRV'],1,5)
    df = FormTableForPAPIAnalysis(result)
    kernels = np.unique(df[Common.KERNEL])
    iters   = np.unique(df[Common.ITER])
    ranks   = np.unique(df[Common.PID])
    sizes   = np.unique(df[Common.CLASS])
    metrics = np.unique(df[Common.PAPI])
    
    # intra size - intra rank
    print "Across iterations"
    for kernel in kernels:
        print kernel
        x = PrettyTable(["Metric", "max", "min", "mean","std"])
        x.align["Metric"] = "l"
        x.padding_width = 1
        for metric in metrics:
            dist = []
            for size in sizes:
                for rank in ranks:
                    strList = df[(df[Common.KERNEL] == kernel) & (df[Common.PAPI] == metric) & \
                                 (df[Common.CLASS] == size) & (df[Common.PID] == rank) ][Common.SAX].values
                    dist.extend(Common.EnumerateDistance(strList,strList,False,True))
            dist = np.array(dist)
            x.add_row([metric,np.amax(dist), np.amin(dist), np.mean(dist),np.std(dist)])
        print x.get_string(sortby="mean")
        
    # intra size - inter rank
    print "Across Ranks"
    for kernel in kernels:
        print kernel
        x = PrettyTable(["Metric", "max", "min", "mean","std"])
        x.align["Metric"] = "l"
        x.padding_width = 1
        for metric in metrics:
            dist = []
            for size in sizes:
                listSax = []
                for rank in ranks:
                    strList = df[(df[Common.KERNEL] == kernel) & (df[Common.PAPI] == metric) & \
                                 (df[Common.CLASS] == size) & (df[Common.PID] == rank) ][Common.SAX].values
                    listSax.append(strList)
                for i in range(len(listSax)):
                    for j in range(i+1,len(listSax)):
                        dist.extend(Common.EnumerateDistance(listSax[i],listSax[j]))
                        
            dist = np.array(dist)            
            x.add_row([metric,np.amax(dist), np.amin(dist), np.mean(dist),np.std(dist)])
        print x.get_string(sortby="mean")
    # inter size - inter rank
    print "Across problem sizes"
    for kernel in kernels:
        print kernel
        x = PrettyTable(["Metric", "max", "min", "mean","std"])
        x.align["Metric"] = "l"
        x.padding_width = 1
        for metric in metrics:
            dist = []
            listSax = []
            for size in sizes:
                strList = df[(df[Common.KERNEL] == kernel) & (df[Common.PAPI] == metric) & \
                             (df[Common.CLASS] == size) ][Common.SAX].values
                listSax.append(strList)
            for i in range(len(listSax)):
                for j in range(i+1,len(listSax)):
                    dist.extend(Common.EnumerateDistance(listSax[i],listSax[j]))
                        
            dist = np.array(dist)            
            x.add_row([metric,np.amax(dist), np.amin(dist), np.mean(dist),np.std(dist)])
        print x.get_string(sortby="mean")
    
    print "Across kernels"
    x = PrettyTable(["Metric", "max", "min", "mean","std"])
    x.align["Metric"] = "l"
    x.padding_width = 1
    for metric in metrics:
        dist = []
        
        listSax = []
        for kernel in kernels:
            strList = df[(df[Common.KERNEL] == kernel) & (df[Common.PAPI] == metric)][Common.SAX].values
            listSax.append(strList)
        for i in range(len(listSax)):
            for j in range(i+1,len(listSax)):
                dist.extend(Common.EnumerateDistance(listSax[i],listSax[j]))
                        
        dist = np.array(dist)            
        x.add_row([metric,np.amax(dist), np.amin(dist), np.mean(dist),np.std(dist)])
    
    print x.get_string(sortby="mean")

            
if __name__ == "__main__":
    IPFDAnalysisAcrossKernels()
