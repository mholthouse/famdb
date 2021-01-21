import os
import pickle
  
#-------------- MAIN PROGRAM ---------------------

# read pickled db, fdb
#f = open(os.path.dirname(os.path.realpath(__file__))+"/INDIx.db","rb")
os.chdir("/Users/mholthouse.wpss.000/Dropbox/Projects/dj/mysite/famdb")
#os.chdir("/Users/mholthouse.wpss.000/Dropbox/Projects/roots")
f = open("INDI.db","rb")
db = pickle.load(f, encoding="latin1")
f.close()
#f = open(os.path.dirname(os.path.realpath(__file__))+"/FAMbin.db","rb")
f = open("FAM.db","rb")
fdb = pickle.load(f, encoding="latin1")
f.close()
print ("Loaded",len(db),"INDI,",len(fdb),"FAM records")

showRNs = False

def getField(entry,keys):
#    print("getField",entry,keys)
    for k in keys:
        #print("  k=",k)
        if not k in entry:
            #print("---> None")
            return None
        entry = entry[k]
    return entry

def fixNumericDate(date):
    if date.isdigit():
        if len(date) == 8:          # ddmmyyyy
            if (int(date[0:2]) <= 31 and int(date[2:4]) <= 12 and date[4:8] == '0000'):
                return date
            if (int(date[0:2]) <= 31 and int(date[2:4]) <= 12
                and int(date[4:8]) > 1500 and int(date[4:8]) < 2022):
                return date
        elif len(date) == 4:            # yyyy
            if (int(date) > 1500 and int(date) < 2020):
                return '0000'+date
    return date

def fixDatePhrase(date):
    if date=='':
            return date
    if date=='unknown':
         return ''
    if date[0:3] == 'c. ':
        date = fixNumericDate(date[3:])
        return 'c'+date
    elif date[0:2] in ['c ','@ ','c.']:
        date = fixNumericDate(date[2:])
        return 'c'+date
    elif date[0] in ['c','@','C']:
        date = fixNumericDate(date[1:])
        return 'c'+date
    else:
        date = fixNumericDate(date)
    return date

def formatDateYear(date):
#    Get into standard form [c]ddmmyyyy
     d = fixDatePhrase(date)
     s = ''
     if len(d)==9 and d[0]=='c' and d[1:].isdigit():
         s += "c."
         d = d[1:]
     if len(d)==8 and d.isdigit():
          if d[4:8] == '0000':
               s += '????'
          else:
               s += d[4:8]
     else:
          s += date
     return s

def checkDate(date):
# return true if valid pure numeric date, false for random date string
    if (len(date)==8 and date[0:2] >= '00' and date[0:2] < '32'
        and (date[2:4] > '00' and date[2:4] < '13' or date[0:4] == '0000')
        and date[4:8] > '1400' and date[4:8] <= '2021'):
        return True
    return False

def formatDate(date):  # return datestring or ''
    month = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec']
    if date == None or date == '':
        return ''
    s = ''
    if date[0] == 'c':      # handle approximate date
        s = 'c.'
        date = date[1:]
    if not checkDate(date):  # random date string
        return date
    s += date[4:8]
    if date[2:4] != '00':
        s = month[int(date[2:4])-1]+" "+s
    if date[0:2] != '00':
        s = date[0:2] + " " + s
    return s         # yyyy, mmm yyyy, or dd mmm yyyy
     
def formatName(rn):
    # rn can be an RN int, or a string that's the name itself to be returned
    global showRNs
    if type(rn) != int:
        return rn
    if not rn in db:
         return "unknown RN="+str(rn)
    s = db[rn]['NAME']['GIVN']              # should have GIVN
    if 'SURN' in db[rn]['NAME']:
         s += " "+ db[rn]['NAME']['SURN']
    if showRNs:
        s += "  RN="+str(rn)
        
    # add date(s) in parens if we know either
    bdate = getField(db[rn],['BIRT','DATE'])
    if bdate == None:
        bdate = '????'
    else:
        bdate = formatDateYear(bdate)
        
    ddict = getField(db[rn],['DEAT'])
    if ddict == None:
        ddate = '    '      # still living
    else:
        ddate = getField(ddict,['DATE'])
        if ddate == None:
            ddate = '????'     # died, don't know when
        else:
            ddate = formatDateYear(ddate)
    if bdate == '????' and ddate == '????':
        return s
    s += "  ("+bdate+"-"+ddate+")"             
    return s

def findParents(child):
    for famID in fdb:
        f = fdb[famID]
        if 'CHILDlist' in f:
            if str(child) in f['CHILDlist']:
                husb = f['HUSB']
                husb = int(husb) if husb.isdigit() else husb
                wife = f['WIFE']
                wife = int(wife) if wife.isdigit() else wife
                return (husb, wife)
    print ("***WARNING: no family found for child RN="+str(child))
    return ('','')

def findDescendants(person, level, limit):
     global n
     n += 1
     if level > limit:
         return
     if not person.isdigit():      # until RNs created for parents
          print ("   "*level + str(level) +"  "+person)
          return
     
     rn = int(person)
     s = "   "*level + str(level) +"  "+ formatName(rn)
     print (s)

     if rn == 0 or not 'FAMlist' in db[rn]:
         return
     fams = db[rn]['FAMlist']
     for famID in fams:
          f = fdb[famID]
          if f['WIFE'] == str(rn):
              spouse = f['HUSB']
          else:
              spouse = f['WIFE']
          print ("   "*(level + 1) + formatName(int(spouse)))
          if 'CHILDlist' in f:
              for child in f['CHILDlist']:
                  findDescendants(child,level+1, limit)
     return


def findAncestors(person, level):
     global n
     n += 1
     if not person.isdigit():      # until RNs created for parents
          print ("   "*level + str(level) +"  "+person)
          return
     
     rn = int(person)
     s = "   "*level + str(level) +"  "+ formatName(rn)
     print (s)
     
     for famID in fdb:
          f = fdb[famID]
          if 'CHILDlist' in f  and str(rn) in f['CHILDlist']:
                   #print famID
                   if 'HUSB' in f and f['HUSB'] != '':
                        findAncestors(f['HUSB'],level+1)
                   if 'WIFE' in f and f['WIFE'] != '':
                        findAncestors(f['WIFE'],level+1)
                   return

def findA(rn):
    global n
    n = 0
    findAncestors(str(rn),1)
    print (n,"ancestors found")
  
def findDLim(rn,limit):
    global n
    n = 0
    findDescendants(str(rn),1,limit)
    print (n,"descendants found")
    
def findD(rn):
    global n
    n = 0
    findDescendants(str(rn),1,99)
    print (n,"descendants found")

def allIn(string,record):
        strings = string.lower().split(' ')
        r = record.replace("'","") # remove dict punctuation
        r = r.replace(":","")
        r = r.replace("{","")
        r = r.replace("}","")
        r = r.replace(",","")
        r = r.replace('"',"")   # nicknames
        r = r.replace("/"," ")  # Fay/Faye, etc.
        r = r.lower()
        recordNames = r.split(' ')
        found = True
        for s in strings:
            if not s in recordNames:
                found = False
                break
        return found
    
def searchName(name):
    rns = []
    for d in db:
        nstring = str(db[d]['NAME'])
        if allIn(name,nstring):
            rns.append(d)
    name_rn = []
    for rn in rns:
        name_rn.append([formatName(rn),rn])
    name_rn.sort()
    return name_rn

def find(string):
    print ("INDIVIDUALS")
    for d in db:
        dstring = str(db[d])
        if string in dstring:
            print (db[d])
    print ("\nFAMILIES")
    for f in fdb:
        fstring = str(fdb[f])
        if string in fstring:
            print (fdb[f])
                 
def formatRN(rn):
##    data =  createDB.convertToRoots(rn,db,fdb)
##    processRootsDB.printRecord(rn,data,db)
##

    s= "\n-------------------------------------\n"
    s+= formatName(rn)+"\n"
    changed = getField(db[rn],('CHAN','DATE'))
    s+= "   (Last updated "+formatDate(changed)+")\n\n"

    father, mother = findParents(rn)
    s+= "FATHER: "+formatName(father)+"\n"
    s+= "MOTHER: "+formatName(mother)+"\n"
    bdate = getField(db[rn],('BIRT','DATE'))
    bplace = getField(db[rn],('BIRT','PLAC'))
    if bdate != None and len(bdate) > 0:
        s+= "BORN: "+formatDate(bdate)+"\n"
        if bplace != None and len(bplace) > 0:
            s+= "  AT: " +bplace+"\n"
    elif bplace != None and len(bplace) > 0:
        s+= "BORN AT: " +bplace+"\n"

# get spouses and children
    fams = db[rn]['FAMlist']  # should always be there even if empty
    children = []
    marriages = []
    for f in fams:
        m = ['']*4
        if fdb[f]['HUSB']==str(rn):
            m[0] = fdb[f]['WIFE']
            m[3] = getField(fdb[f],('MARR','Wstatus'))
        else:
            m[0] = fdb[f]['HUSB']
            m[3] = getField(fdb[f],('MARR','Hstatus'))        
        m[1] = getField(fdb[f],('MARR','DATE'))
        m[2] = getField(fdb[f],('MARR','PLAC'))    
        marriages.append(m)
        # add children from marriage
        clist = fdb[f]['CHILDlist']
        for c in clist:
            children.append(c)

    if len(marriages) > 0:
        s+= "NUMBER OF MARRIAGES: "+str(len(marriages))+"\n"
    for i,m in enumerate(marriages):
        spouse = m[0]
        mdate = m[1]
        mplace = m[2]
        mstatus = m[3]
        s+= "MARRIED TO: "
        if i > 0:
            s+= "ReMARRIED TO: "
        s+= formatName(int(spouse))+"\n" 
        if mdate != None and len(mdate) > 0:
            s+= "        ON: "+formatDate(mdate)+"\n"
        if mplace != None and len(mplace) > 0:
            s+= "        AT: "+mplace+"\n"
        mstati = {"M":"Married","W":"Widowed","D":"Divorced"," ":"unknown"}
        if mstatus != None:
            s+= "        STATUS: "+mstati[mstatus]+"\n"

    ddate = getField(db[rn],('DEAT','DATE'))
    dplace = getField(db[rn],('DEAT','PLAC'))
    if ddate != None:
        s+= "DIED ON: "+formatDate(ddate)+"\n"
        if dplace != None:
            s+= "  AT: "+dplace+"\n"
    elif dplace != None:
        s+= "DIED AT: "+dplace+"\n"
    else:
        raddress = getField(db[rn],('RESI','ADDR'))
        if raddress != None:
            s+= "LIVING AT: "+raddress+"\n"
            
    if len(children) > 0:
        s+= "NUMBER OF CHILDREN: "+str(len(children))+"\n"
    for i,c in enumerate(children):
        if c.isdecimal():
            name = formatName(int(c))
        else:
            name = c
        s+= "    "+str(i+1)+") "+name+"\n"

    return s

def findName(nameString):
    name_rn = searchName(nameString)
    for n in name_rn:
        print(str(n[1])+'\t'+n[0])

def printRN(rn):
    print(formatRN(rn))
    
    
commands = ("findA(rn) - ancestors\n"
+ "findD(rn) - descendants\n"
+ "findDLim(rn,generations)\n"
+ "find('strings')\n"
+ "findName('names')\n"
+ "printRN(rn)\n"
+ "commands\n"
+ "showRNs = True(default) or False")

print (commands)









