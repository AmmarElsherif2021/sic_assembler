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
"""
#.............................................................................................
def fixTAddress(inst_set):
    inst_set['OPCODEVAL']=inst_set.apply(lambda row: int(row.OPCODEVAL,16), axis = 1)
    
    #OPCODE in binary.......................................
    #Discard the excessive right bits for formats 3,4 OPCODE
    inst_set['OPCODEVAL']=inst_set.apply(lambda row: row.OPCODEVAL/4 if row.FORMAT in [3,4] and row.OPCODEVAL>63 else int(row.OPCODEVAL)/1, axis = 1)
    
    #OPCODE represented in 8 bits in formats 1,2 and in 6 bits for formats 3,4 OPCODE
    inst_set['OPCODEVAL']=inst_set.apply(lambda row: format(row.OPCODEVAL,'08b') if row.FORMAT in [1,2] else format(int(row.OPCODEVAL),'06b'), axis = 1)

    #calculate displacement -- Format 3
    #  get PC column
    inst_set['PC']=inst_set.apply(lambda x: 0, axis = 1)
    for i in range(len(inst_set['LOCCTR'])-1):
        inst_set['PC'][i]=inst_set['LOCCTR'][i+1]
    
    #get BASE LOCCTR
    BASE_op=inst_set.loc[inst_set['OPCODE']=='BASE']['OPERAND'].values[0]
    BASE_loc=inst_set.loc[inst_set['REF']==BASE_op]['LOCCTR'].values[0]
    #print('>>>>>>>',BASE_op,'BASE_loc>>>>>>',BASE_loc)
    
    #  get displacement handle p,b flags bits:
    inst_set['TADD']=inst_set.apply(lambda x: x.TADD - x.PC if x.FORMAT==3 else x.TADD, axis=1)
    inst_set['p']=inst_set.apply(lambda row:1 if row.TADD<2047 and row.TADD>-2048 and row.FORMAT==3 else 0, axis = 1)    
    inst_set['TADD']=inst_set.apply(lambda x: x.TADD + x.PC -BASE_loc if (x.FORMAT==3 and x.p==0) else x.TADD , axis=1)
    inst_set['b']=inst_set.apply(lambda row: 1 if row.p==0 and row.FORMAT==3 else 0, axis = 1)
    
    #  handle negative displacements for binaries
    inst_set['TADD']=inst_set.apply(lambda x: (-(x.TADD) + 4080) if (x.FORMAT==3 and x.TADD<0 and x.TADD>=-15) else x.TADD , axis=1)
    inst_set['TADD']=inst_set.apply(lambda x: (-(x.TADD) + 3840) if (x.FORMAT==3 and x.TADD<0 and x.TADD>=-255) else x.TADD , axis=1)

    
   
    #Represent Disp/Address in  bits -- format3 , format 4 
    inst_set['TADD']=inst_set.apply(lambda row:format(row.TADD,'08b') if row.FORMAT==4 else format(row.TADD,'012b'), axis = 1)
    
    #Represent R1 and R2 -- format 2
    inst_set['R1']=inst_set.apply(lambda row: format(row.R1,'04b'), axis = 1)
    inst_set['R2']=inst_set.apply(lambda row: format(row.R2,'04b'), axis = 1)
    
    # delete excessive columns
    col_del=['REF','OPERAND','signal','PC']
    for col in col_del:
        del inst_set[col]
        
    
    return inst_set
    


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


"""
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
