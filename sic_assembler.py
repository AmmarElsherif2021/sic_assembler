# -*- coding: utf-8 -*-
"""
Created on Tue Jan 10 19:02:02 2023

@author: ammar
"""
import math
import pandas as pd
import re
from ast import literal_eval

#------------------------------------------------------------------------------
#read json file: A reference file of SIC/XE instructions:

sic_inst0 = pd.read_json("inst.json" )
sic_inst=sic_inst0.transpose()


sic_inst.reset_index(inplace=True)
sic_inst = sic_inst.rename(columns = {'index':'OPCODE'})
print("\n","Set of SIC instructions reference","\n")

print(sic_inst)
print('------------------------------------------------------------') 
  
    
# read txt file of instructions input:      


input_set = pd.read_csv("input_file.txt", sep=".", header=None, names=["atts"], skiprows=0 ,skipinitialspace =True)
input_set['REF'],input_set['OPCODE'],input_set['OPERAND'] = zip(*input_set['atts'].str.split())
del input_set['atts']

print("\n","Set of input instructions imported from test.txt","\n")
print(input_set)

#Function to convert df values to suitable data types
def convertDataType(df):
    
    df=df.astype(str)
    return df
#Merge sicxe_insts and input dataframes and add looctr col.-------------------------------


def createLocctr(inst_set,sic,firstloc=0):
    
    #merge the two dataframes
    inst_set1= pd.merge(sic,inst_set,on='OPCODE', how='right', copy='False')
    
    #create LOCCTR
    inst_set1['LOCCTR']=inst_set1.apply(lambda x: 0 , axis=1)
    inst_set1=inst_set1.astype(str)     
    
    
    #fill LOCCTR
    init_loc=hex(0)
    current_loc=init_loc
    inst_set1['LOCCTR'][0]=init_loc
    locctr=list()
    locctr.append(current_loc)
    i=1
    increment=hex(0)
    while i<(len(inst_set1['LOCCTR'])):
        if inst_set1['OPCODE'][i]=='BYTE':
            if re.findall(r'^C',inst_set1['OPERAND'][i]):
                digits=re.findall(r"[^C,']",inst_set1['OPERAND'][i])
                increment=hex(len(digits))
            else:
                digits=re.findall(r"[^X,']",inst_set1['OPERAND'][i])
                increment=hex(int((len(digits)+1)/2))
            
        elif inst_set1['OPCODE'][i]=='WORD':
            increment=hex(3)
        elif inst_set1['OPCODE'][i]=='RESW':
            increment=hex(3*int(inst_set1['OPERAND'][i]))
        elif inst_set1['OPCODE'][i]=='RESB':
            increment=hex(int(inst_set1['OPERAND'][i]))
        else:
            increment=hex(3)
        current_loc=hex(int(current_loc,16)+int(increment,16))
        locctr.append(current_loc)
        i+=1
    
    for i in range(len(locctr)-1):
        inst_set1['LOCCTR'][i+1]=locctr[i]
    
    return inst_set1

#.................................................................................

def get_symtab(inst_set):
    df=pd.DataFrame()
    df=inst_set[['REF','LOCCTR']]
    return df
    
      

        
print('\n************************** END OF SIC/XE ASSEMBLER PASS 1 ****************************************')
 #PASS 2........................................................................................

#.......................................................................................        


#Filling x,address columns
def fill_Taddress(inst_set):
   
    #assure inst_set values data type
    inst_set=inst_set.astype(str)
    del inst_set['Format']
    #call symtab:
    symtab=get_symtab(inst_set)
    
    #Add x,TADD columns
    inst_set['x']=inst_set.apply(lambda x:int(bool(re.findall(r",X",x.OPERAND))) , axis=1)
    inst_set['OPERAND']=inst_set.apply(lambda x: ''.join(re.findall(r"[^,X$]" ,x.OPERAND)) if x.OPERAND != 'INDEX' else x.OPERAND,axis=1 )
    #add TADD columns
    inst_set['TADD']=inst_set.apply(lambda x:0,axis=1)
    
    for j in range(len(inst_set['OPERAND'])):
        if inst_set['OPERAND'][j] != 'nan':
            for i in range(len(symtab['REF'])):
                if inst_set['OPERAND'][j]==symtab['REF'][i]:
                    inst_set['TADD'][j]=symtab['LOCCTR'][i]
            
        
    return inst_set

#.......................................................................................
def convertToBinary(inst_set):
    #assure inst_set values data type
    inst_set=inst_set.astype(str)
    
    inst_set['TADD']=inst_set.apply(lambda x: format(int(x.TADD,16),'015b') if x.TADD!='0' else '0' ,axis=1)
    
    inst_set['OPCODEVAL']=inst_set.apply(lambda x: format(int(x.OPCODEVAL,16),'08b') if x.OPCODEVAL!='nan' else 'nan', axis=1)
    
    
    return inst_set    

#.............................................................................................



def collectHTE(inst_set):
    
    #create objcode column 
    inst_set['OBJCODE']=inst_set.apply(lambda x:int(int((x.OPCODEVAL+x.TADD),2)>0)+int(x.OPCODE=='BASE') , axis=1)
    
    #concatenate bits in OBJCODE col
    inst_set = inst_set.astype(str)
    inst_set['OBJCODE']=inst_set.apply(lambda r :(r.OPCODEVAL+r.n+r.i+r.x+r.p+r.e+r.TADD)
                                       if r.FORMAT in [3,4] else (r.OPCODEVAL+r.n+r.i+r.x+r.p+r.e+r.R1+r.R2) ,axis=1)
    
    #turn objcode into hexa
    inst_set['OBJCODE']=inst_set.apply(lambda x: hex(int(x.OBJCODE,2)), axis=1)
    Hstr='H.XXXXXX.000000.000000'
    Tstr='T.000000.00.000000'
    Estr='E.000000'
    
    return inst_set



input_set1=createLocctr(input_set,sic_inst,0)
print('input_set 1 >>>>>>>>>>>')
print(input_set1)
#..................................
symtab=get_symtab(input_set1)
print('symtab >>>>>>>>>>>')
print(symtab)
#..................................
input_set2=fill_Taddress(input_set1)
print(input_set2)
#.................................
input_set3=convertToBinary(input_set2)
print(input_set3)
