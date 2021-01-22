import os
import readNamelist
import processRootsDB
import pickle
from utils import *

maleNames = ['Andreas','Carl','Christian','Daniel','David','Elwood','Gary',
             'George','Gustavus','Jakob','Johannes','John','Joseph','Kenneth',
             'Levi','Ralph','Richard','Tanner','Thomas','Wesley','William']
femaleNames = ['Agnes','Alta','Amanda','Anne','Ashley','Barbara','Catherine',
               'Clara','Doris','Etta','Fanny','Jamie','Joan','Katharina',
               'Katherine','Lisa','Lois','Marie','Mary','May','Pamela',
               'Pauline','Susanna']
debug = False

# combine a name and possible surname for reporting
def formatName(db,rn):
    if rn not in db:
        print("WARNING:  RN "+str(rn)+" not in db")
        s = ("RN "+str(rn)+"not in DB")
        return s
    s = db[rn]['NAME']['GIVN']              # should have GIVN
    if 'SURN' in db[rn]['NAME']:
         s += " "+ db[rn]['NAME']['SURN']
    return s

def getMarriages(db,fdb,rn):
    marriages1 = db[rn]['FAMlist']
    marriages = []        # linear search of all families
    for famID in fdb:
        f = fdb[famID]
        if f['HUSB'] == str(rn) or f['WIFE'] == str(rn):
            marriages.append(famID)
    m = marriages[:]
    if m.sort() !=  marriages.sort():
        print ("WARNING: RN="+str(rn)+": FAMlist"+str(marriages1)
               +" != searchlist"+str(marriages))
    return marriages1

def findFamily(fdb, person1, spouse):
    for famID in fdb:
        f = fdb[famID]
        if (f['HUSB'] == person1 and f['WIFE'] == spouse or
            f['WIFE'] == person1 and f['HUSB'] == spouse):
            return famID
    return None

def findParents(fdb, child):
    for famID in fdb:
        f = fdb[famID]
        if 'CHILDlist' in f:
            if str(child) in f['CHILDlist']:
                return (f['HUSB'], f['WIFE'])
    return ('','')


def getDates(db,rn):
    if 'BIRT' in db[rn] and 'DATE' in db[rn]['BIRT']:
            bdate = db[rn]['BIRT']['DATE']
    else:
            bdate = ''
    ddate = ''
    if 'DEAT' in db[rn] and 'DATE' in db[rn]['DEAT']:
            ddate = db[rn]['DEAT']['DATE']
    return bdate,ddate

# try to match two NAME blocks where one may have more info
# return True if different, or False and a combination name to use
#
def compareNames(rn1,rn2):    
    name1 = formatName(rn1)
    name2 = formatName(rn2)
    diff, name = compareNameStrings(name1, name2)
    return diff, name

# try to match a non-RN name string with an RN one
def findName(db,name):
    for rn in range(11629,len(db)+1):
        n1,b1,d1 = extractDates(name)
        if len(n1) > 10 or ' ' in n1:
            n2 = formatName(db, rn)
            if n1 != n2:
                continue
            b2,d2 = getDates(db,rn)
            diff,bdate,ddate = compareDates(b1,d1,b2,d2)
            if diff:
                #print(rn,"\t",b2,"\t",d2,"\tno match\t",name)
                continue
            else:
                #print(rn,"\t",b2,"\t",d2,"\tmatch\t",name,"\tuse\t",bdate,"\t",ddate)
                return rn
    return 0

def getSpouses(f):
    return (int(f[:f.index('+')]),int(f[f.index('+')+1:]))

def ifdebug(msg):
    global debug
    if debug:
        print(msg)
        
def addNewINDI(db,name,sex):
    global debug
    nextRN = max(db.keys()) + 1
    if debug:
        print("addNewINDI",name,sex,"->",nextRN)

    # check if already there
    name = name.strip()
    rn = findName(db,name)
    if rn != 0:
        if debug:
            print("addNewINDI",name,sex,"-> found match",rn)
        return rn

    # create new    
    cleanName, bdate, ddate = extractDates(name)
    db[nextRN] = {}
    db[nextRN]['rn'] = nextRN   
    db[nextRN]['NAME'] = {}
    db[nextRN]['NAME']['GIVN'] = cleanName
    if bdate != '':
        db[nextRN]['BIRT'] = {'DATE':bdate}
    if ddate != '':
        db[nextRN]['DEAT'] = {'DATE':ddate}
    db[nextRN]['SEX'] = sex
    db[nextRN]['FAMlist']=[]
    return nextRN



# create new family, append to FAMlists of spouses
def addNewFAM(db,fdb,rn,spouseRN):
    famID = str(rn)+'+'+str(spouseRN)
    ifdebug("adding new family "+famID)
    fdb[famID]={}
    if db[rn]['SEX'] == 'F':
        fdb[famID]['HUSB'] = str(spouseRN)
        fdb[famID]['WIFE'] = str(rn)
    else:
        fdb[famID]['WIFE'] = str(spouseRN)
        fdb[famID]['HUSB'] = str(rn)
    fdb[famID]['MARR'] = {}
    fdb[famID]['CHILDlist'] = []
    db[rn]['FAMlist'].append(famID)
    db[spouseRN]['FAMlist'].append(famID)
    return famID

def getField(entry,key1,key2):
    if len(key2)==0:
        return entry[key1] if key1 in entry else ''
    return entry[key1][key2] if (key1 in entry
                              and key2 in entry[key1]) else ''
                        

#-----------------------------------------------------------------
# for each RN, check that RN parents match with family record
# if only one RN with noRN or unknown
#    check this one to be listed unassigned
#    try to match with a non-RN spouse, or add [to] "uncertain spouse"
# if two noRN parents or one and an unknown, create a new family
#     check all created names afterward for possible dups
# two unknowns shouldn't happen
#-----------------------------------------------------------------
def createPass3(db,fdb,rdb):
    return




#-----------------------------------------------------------------
# helper functions for pass2
#-----------------------------------------------------------------


def removeEmpty(wlist):         # get rid of double space null words
    while wlist.count('') > 0:
        wlist.remove('')
    return wlist

# try to match two names (dates at end have been removed already)
# match initials to full names
# return a name if it has a superset of the words of the other
def matchName(name1,name2):
    if name1 == name2:          #handle empty strings
        return True,name1
    if name1 == '' or name2 == '':
        return False,''
    
    #print("matchName",name1,name2)
    orig1 = name1.split(' ')        # save originals
    orig2 = name2.split(' ')
    words1 = removeEmpty(name1.lower().split(' '))   # ignore case
    words2 = removeEmpty(name2.lower().split(' '))
    for i in range(min(len(words1),len(words2))):       # match initials
        if (words1[i][0]+'.' == words2[i]
            or words1[i][0] == words2[i]):
            name2 = name2.replace(orig2[i],orig1[i])
            words2[i] = words1[i]
        if (words2[i][0]+'.' == words1[i]
            or words2[i][0] == words1[i]):
            words1[i] = words2[i] 
            name1 = name1.replace(orig1[i],orig2[i])

    w1 = set(words1)  # if all words of one in other, use the superset
    w2 = set(words2)
    if (w1.issuperset(w2)):
        return True,name1
    elif (w2.issuperset(w1)):
        return True,name2
    
    return False,''

# normalize a no-RN name string <name>[(bdate)[-<ddate>])]
# to <name>,bdate,ddate - dates [c.]yyyymmdd or '' for none
def normalizeNameString(nameString):
    nameString = nameString.strip()
    name,bdate,ddate = extractDates(nameString)  # get strings
    if bdate == None:
        bdate = ''
    if ddate == None:
        ddate = ''
    return name,bdate,ddate

def normalizeChildlist(children):
    for i in range(len(children)):    # normalize any no-RN names
        if not children[i].isdigit():
            name,bdate,ddate = normalizeNameString(children[i])   
            children[i] = formatNoRNName(name,bdate,ddate)

# format name and dates -> name (bdate[-ddate]) | (d. ddate)
def formatNoRNName(name,bdate,ddate):
    # create a new name with best of both
    s = name
    if bdate != '':
        s += " ("+formatNoRNDate(bdate)
        if ddate != '':
            s += "-"+formatNoRNDate(ddate)
        s += ')'
    elif ddate != '':
        s += " (d. "+formatNoRNDate(ddate)+')'
    return s

# Names have been normalized already
def matchNoRNNames(nameString1,nameString2):
    nameString1 = nameString1.strip()
    nameString2 = nameString2.strip()
    if nameString1 == nameString2:
        return True,nameString1
    name1,bdate1,ddate1 = extractDates(nameString1)
    name2,bdate2,ddate2 = extractDates(nameString2)
    match,name = matchName(name1,name2)
    if not match:
        #print("name\t",nameString1,"\n\t",nameString2,"\n")
        return False,''
    diff,bdate,ddate = compareDates(bdate1,ddate1,bdate2,ddate2)
    if diff:
        #print("date\t",nameString1,"\n\t",nameString2,"\n")
        return False,''
    return True,formatNoRNName(name,bdate,ddate)

# match items one-by-one in lists of matching length
# update lists with best of two matching names
# if in different order, some won't match
def matchNameLists(list1,list2):
    allMatch = True
    for i in range(len(list1)):
        if list1[i] == list2[i]:
            continue
        match,newname = matchNoRNNames(list1[i],list2[i])
        if match:
            list1[i] = newname
            list2[i] = newname
        else:
            allMatch = False
    return allMatch

# try to find name in namelist (all normalized)
def findNoRNName(name,namelist):
    for i in range(len(namelist)):
        match,newname = matchNoRNNames(name,namelist[i])
        if match:
            return True,newname,i
        match,newname = matchAnyPart(name,namelist[i])
        if match:
            return True,newname,i
    return False,'',-1

def matchAnyPart(name1,name2):
    s1 = set(name1.split(' '))
    s2 = set(name2.split(' '))
    intersect = s1.intersection(s2)
    if len(intersect) > 1:
        name = name1 if len(name1) >= len(name2) else name2
        #print("matched\t",name1,"\n\t",name2,"\t",name,"\n")
        return True,name
    return False,''

def printChildren(db,rdb,clist):
    s = ''
    for c in clist:
        if not c.isdigit() or c == '0':
            continue
        s += "\t\t"+c+":  "+formatName(db,int(c))
        s += "  ("+formatDate(getField(db[int(c)],'BIRT','DATE'))
        s += ")  M:"+rdb[int(c)][5]+"   F:"+rdb[int(c)][6]+"\n"
    return s

def inserted(s1,s2):
    if len(s1)>len(s2):
        big = s1
        small = s2
    else:
        big = s2
        small = s1
    for i in range(len(small)):
        if big[i] != small[i]:
            break
    jb = len(big)-1
    js = len(small)-1
    while js >= i:
        if big[jb] != s2[js]:
            break
        jb -= 1
        js -= 1
    return small[i:js+1],big[i:jb+1]


def diffLists(s1,s2):
    diffs = [0,0,0,0,0,0,0,0,0]
    diffword = ''
    for i in range(len(s1)):
        if s1[i] != s2[i]:
            diffs[0] += 1
            diffwords = [s1[i],s2[i]] 
            #print(s1[i],s2[i])
        s1a = s1[i].split(' ')
        s2a = s2[i].split(' ')
        for j in range(min(len(s1a),len(s2a))):
            if s1a[j] != s2a[j]:
                diffs[1] += 1
                #print(s1a[j],s2a[j])
                for k in range(min(len(s1a[j]),len(s2a[j]))):
                    if s1a[j][k] != s2a[j][k]:
                        diffs[2] += 1
                        #print(s1a[j],s2a[j])
                diffs[2] += abs(len(s1a[j])-len(s2a[j]))
        diffs[0] += abs(len(s1a)-len(s2a))
##    if (diffs[0] == 1 and diffs[1] == 1):  
##        print(diffs,"\t",diffwords[0],"\t",diffwords[1])
    return diffs
    
def getChildlist(rn,db):
    clist = []
    for f in db[rn]['FAMlist']:
        if 'CHILDlist' in fdb[f]:
            clist = clist + fdb[f]['CHILDlist'] if 'CHILDlist' in fdb[f] else []
    return clist   

def printRNChildren(rn,db,fdb,rdb):
    print(rn,"\t",formatName(db,rn),"\t\t",rdb[rn][8],"\n",rn,"\t\t\t",getChildlist(rn,db))
    for f in db[rn]['FAMlist']:
        s1,s = getSpouses(f)
        if rn != s1:
            s = s1
        clist = []
        if s < 11629: 
            print(rn,"\t",s,"\t",formatName(db,s),"\t",rdb[s][8])
        else:
            print(rn,"\t",s,"\t",formatName(db,s),"\t",getField(fdb[f],'MARR','DATE'))
        clist = fdb[f]['CHILDlist'] if 'CHILDlist' in fdb[f] else "<none>"
        print(rn,"\t\t\t",clist)
    print("\n")

# compare Roots RN childlists with combined fdb childlists for RN
def checkRNChildren(db,fdb,rdb):
    n = [0,0,0,0,0,0,0,0]
    n1 = ['=',"good enough",'matched','sorted=','len =','len !=      ','no CHILDlist']
    for rn in range(1,11629):
        rdbList = rdb[rn][8].copy()
        dbList = []
        for f in db[rn]['FAMlist']:
            if not 'CHILDlist' in fdb[f]:
                n[7]+=1
            else:
                dbList += fdb[f]['CHILDlist']
        normalizeChildlist(rdbList)
        normalizeChildlist(dbList)
        rdbListS = rdbList.copy()
        rdbListS.sort()
        dbListS = dbList.copy()
        dbListS.sort()
        if str(rdbList) == str(dbList):
            n[0] += 1
        elif str(rdbListS) == str(dbListS):
            #printRNChildren(rn,db,fdb,rdb)
            n[3] += 1
        elif len(rdbList) == len(dbList):
            diffs = diffLists(rdbList,dbList)
            if diffs[0] == 1 and diffs[1] == 1:   # off by one char in one name
                n[1] += 1                       # good enough!
            elif matchNameLists(rdbList,dbList):
                n[2] += 1
            else:
                #printRNChildren(rn,db,fdb,rdb)
                #print(rn,"\t",rdbList,"\n\t",dbList,"\n")
                n[4] += 1
        else:
            #printRNChildren(rn,db,fdb,rdb)
            #print(rn,"\t",rdbList,"\n\t",dbList,"\n")
            n[5] += 1
    print(n)
    print(n1)
    
# check each child RN of a family to see if has the correct parents
def checkChildren(db,fdb,rdb):
    num = rnerr = nameerr = 0
    for f in fdb:       # for each family
        husb = fdb[f]['HUSB']
        wife = fdb[f]['WIFE']
        if not 'CHILDlist' in fdb[f]:
            continue
        for c in fdb[f]['CHILDlist']:   # for each child in family
            if not c.isdigit():       # ignore non-RN children
                continue
            num += 1
            err = ''
            rn = int(c)
            father = rdb[rn][6]
            mother = rdb[rn][5]
            if husb > 11628:
                husbName = formatName(db,husb)
                match,newname = matchNoRNNames(husbName,father)
                #print(match,husbName,father,newname)
                if not match:
                    err += "\tfather\t"+father+"\t"+husbName
                    nameerr += 1
            else:
                if father != str(husb):
                    rnerr += 1
                    err += "\tfather\t"+father+"\t"+str(husb)
            if wife > 11628:
                wifeName = formatName(db,wife)
                match,newname = matchNoRNNames(wifeName,mother)
                #print(match,wifeName,mother,newname)
                if not match:
                    nameerr += 1
                    err += "\tmother\t"+mother+"\t"+wifeName
            else:
                if mother != str(wife):
                    rnerr += 1
                    err += "\tmother\t"+mother+"\t"+str(wife)
            if err != '':
                print(str(rn)+"\t"+f+err)
    print("\npass2 check: ",num,"children,",rnerr,"bad rns +",nameerr,"bad names")

  
# handles multiple families 
errcount = 0
def matchChildren(rn,db,fdb,rdb):
    global debug
    global errcount
    fams = db[rn]['FAMlist']
    rnChildren = rdb[rn][8].copy()
    normalizeChildlist(rnChildren)
    noRNfams = []
    spouses = []
    spouseNames = []
    ifdebug("matching "+str(rn)+" "+str(rnChildren))
    errPrint = False
    err = str(rn)+"\t"+formatName(db,rn)+"\t\t"+str(rnChildren)+"\n"
    for f in fams:
        ignore,spouse = getSpouses(f)
        spouses.append(spouse)      # remember for post-loop processing
        spouseNames.append(formatName(db,spouse))
        err += str(rn)+"\t"+str(spouse)+"\t"+formatName(db,spouse)
        err += " (m "+formatDate(getField(fdb[f],'MARR','DATE'))+")\t"

        # if this is second spouse, common children already in this family
        # so remove them from list to assign, and go on to next family
        if rn == spouse:
            ifdebug("  second spouse in family "+f+" with children "+str(fdb[f]['CHILDlist']))
            for c in fdb[f]['CHILDlist']:
                ifdebug("   checking "+c)
                match,newname,loc = findNoRNName(c,rnChildren)
                if match:
                    ifdebug("    found "+c+" in family")
                    rnChildren.pop(loc)
            continue
        
        if spouse > 11628:      # no RN spouse families have no children yet
            err += "\n"
            noRNfams.append(f)  # but remember them
            continue

        spouseChildren = rdb[spouse][8].copy()
        normalizeChildlist(spouseChildren)
        err += str(spouseChildren)+"\n"
        ifdebug("  with "+f+" "+str(spouseChildren))
        rnChildrenCopy = rnChildren.copy()
        for c in rnChildrenCopy:     # use copy to allow remove from original
            ifdebug("   checking "+c)
            if c.isdigit():             # RN is simple match
                if c in spouseChildren:
                    #print("    found",c)
                    ifdebug("   assigning child "+c+" to "+f)
                    fdb[f]['CHILDlist'].append(c)
                    spouseChildren.remove(c)
                    rnChildren.remove(c)
            else:
                found,name,loc = findNoRNName(c,spouseChildren)
                if found:
                    #print("    found",c)
                    ifdebug("   assigning child "+c+" to "+f)
                    fdb[f]['CHILDlist'].append(name)
                    spouseChildren.pop(loc)   # name may have been changed
                    rnChildren.remove(c)

        ifdebug("  family "+f+" = "+str(fdb[f]['CHILDlist']))
        ifdebug("  remaining children: "+str(rnChildren))
        if len(db[spouse]['FAMlist']) == 1 and spouseChildren != []:
            #print("ERROR 1: RN",rn,"spouse",spouse,"children",spouseChildren,"not found in RN")
            err += str(rn)+"\t...left\t\t"+str(spouseChildren)+"\n"
            err += printChildren(db,rdb,spouseChildren)
            errprint = True

    if rnChildren != []:
        if len(noRNfams) == 1:  # only one nonRN family, assign rest of children there
            fdb[noRNfams[0]]['CHILDlist']= rnChildren
            ifdebug(str(rnChildren)+" assigned to only noRN spouse "+noRNfams[0])
            rnChildren = []
            
        elif noRNfams == []: 
            #print("ERROR 2: RN",rn,"children",rnChildren,"not found in any spouses")
            err += str(rn)+"\tnone\t\t"+str(rnChildren)+"\n"
            err += printChildren(db,rdb,rnChildren)
            errPrint = True

        else:   # try to match child to spouse
            for child in rnChildren.copy():     
                if not child.isdigit():         # match RN child by mother/father name
                    continue
                if db[rn]['SEX'] == 'M':
                    name = rdb[int(child)][5]   # match mother
                else:
                    name = rdb[int(child)][6]   # match father
                match,newname,loc = findNoRNName(name,spouseNames)
                if match:
                    ifdebug("matched parent "+name+" --> "+spouseNames[loc])
                    ifdebug("assigned child "+child+" to "+fams[loc]+" "+spouseNames[loc])
                    rnChildren.remove(child)
                    fdb[fams[loc]]['CHILDlist'].append(child)

    if rnChildren != []:    # weren't able to match all, assign to new "uncertain" spouse        
        #print("WARNING: RN",rn,"children",rnChildren,"assigned to uncertain spouse")
        err += str(rn)+"\tuncert\t\t"+str(rnChildren)+"\n"
        err += printChildren(db,rdb,rnChildren)
        errPrint = True

        #create uncertain spouse and family
        spouseName = "uncertain spouse"+" of "+str(rn)
        spouseSex = 'M' if db[rn]['SEX'] == 'F' else 'F'
        spouseRN = addNewINDI(db,spouseName,spouseSex)
        famID = addNewFAM(db,fdb,rn,spouseRN)  # also updates FAMlists
        fdb[famID]['CHILDlist']=rnChildren
        if debug:
            print("assigned children",rnChildren,"to uncertain spouse family",famID)

    if debug and errPrint:
        print(err)
        errcount += 1
    
    return

#-----------------------------------------------------------------
# for each RN, assign their Roots children to families
# process only families where the RN is the 1st spouse 
# if 2nd spouse has additional families, they'll be handled with that RN
# check that children records have corrent parents
#-----------------------------------------------------------------
def createPass2(db,fdb,rdb):
    global debug
    global n,n1
    nl = "fams, 1-1, 1-1 noRN, 1-1 diff lengths, 1-1 match, 1-1 nomatch, 1-1 2nd spouse"
    for rn in range(1,11639):
        debug = True if rn in [] else False
        
        ifdebug("\n Processing RN "+str(rn))    
        fams = db[rn]['FAMlist']
        nfams = len(fams)
        if nfams == 0:          # no families, skip
            continue
        clist1 = rdb[rn][8]
        ifdebug("assigning RN children "+str(clist1)+" to "+str(fams))
        normalizeChildlist(clist1)
        ifdebug("        normalized to "+str(clist1))

        f = fams[0]
        ifdebug("processing family "+f)
        spouse1rn,spouse2rn = getSpouses(f)
        n[0] += 1
        
        # handle all 1-1 cases
        if len(fams) == 1 and len(db[spouse2rn]['FAMlist']) == 1: # 1-1
            if spouse1rn != rn:         # not first spouse; this fam already handled
                ifdebug("...second spouse of 1-1 family; ignore")
                n[6] += 1
                continue 
            ifdebug("family is 1-1")
            fdb[f]['CHILDlist'] = []  
            n[1] += 1
            if spouse2rn > 11628 or spouse2rn == 0:       # nonRN spouse
                n[2] += 1
                ifdebug("No or NoRN spouse - assigning all to family")
                fdb[f]['CHILDlist'] = clist1   # assign all to family

            else:                                   # RN spouse
                clist2 = rdb[spouse2rn][8]
                normalizeChildlist(clist2)
                ifdebug("spouse children are "+str(clist2))
                if len(clist1) != len(clist2):      # diff # of children, use larger
                    n[3] += 1
                    clist = clist1 if len(clist1)>=len(clist2) else clist2
                    fdb[f]['CHILDlist'] = clist
                    #print("***WARNING: RN",rn,f,"1-1 childlist lengths don't match",
                     #     "\n\t",clist1,"\n\t",clist2)
                elif matchNameLists(clist1,clist2):
                    n[4] +=1
                    fdb[f]['CHILDlist'] = clist1
                else:               # same numbers of children, but don't match
                    n[5] += 1
                    #print("***WARNING: RN",rn,f,"1-1 childlists don't match",
                     #    "\n\t",clist1,"\n\t",clist2)
                    if len(str(clist1)) < len(str(clist2)):  # use longer
                        clist1 = clist2
                    fdb[f]['CHILDlist'] = clist1

        else:       # many to one or many to many
            ifdebug("Family is NOT 1-1 ")
            n[6] += 1
            matchChildren(rn,db,fdb,rdb)

        ifdebug("done with RN "+str(rn))
    print(n)
    print(nl)
    print(errcount,"multi-family errors ")
    


#-----------------------------------------------------------------
# fill out INDI records with BIRT, DEAT, SEX, NOTElist, FAMlist
# create FAM records with HUSB, WIFE, MARR, H+Wstatus, H+WMarrSeq
# create INDI records Uknown and No-RN spouses as needed
#-----------------------------------------------------------------
def createPass1(rn,db,fdb,rdb):
    d = rdb[rn]
    db[rn]['CHAN']={'DATE':d[10]}       # change date

    sex = d[11]                     #sex
    if sex in ("M","F"):
        db[int(rn)]['SEX']=sex
    else:       # handle sex exceptions
        name = db[int(rn)]['NAME']['GIVN'].split(' ')
        if name[0] in maleNames:
            sex = 'M'
        elif name[0] in femaleNames:
            sex = 'F'
        else:
            sex = 'M'
            print ("WARNING: RN="+str(rn)+": "+db[int(rn)]['NAME']['GIVN']
                    +" sex='"+d[11]+"' set to "+sex)
        db[rn]['SEX']=sex

    bdate = d[0]        # birth date, place
    bplace = d[1]
    if len(bdate) > 0:
        btry = fixDate(bdate)
        if btry != None:
            bdate = btry
        db[int(rn)]['BIRT']={'DATE':bdate}
        if len(bplace) > 0:
           db[int(rn)]['BIRT']['PLAC'] = bplace
    elif len(bplace) > 0:
        db[int(rn)]['BIRT']={'PLAC':bplace}
        
    ddate = d[2]        # death date, place
    dplace = d[3]
    if ddate == 'L' and len(dplace) > 0:
        db[int(rn)]['RESI']={'ADDR':dplace}
    else:
        if len(ddate) > 0:
            dtry = fixDate(ddate)
            if dtry != None:
                ddate = dtry
            db[int(rn)]['DEAT']={'DATE':ddate}
            if len(dplace) > 0:
               db[int(rn)]['DEAT']['PLAC'] = dplace
        elif len(dplace) > 0:
            db[int(rn)]['DEAT']={'PLAC':dplace}
    db[int(rn)]['NOTElist']=d[9]
    if debug:
        print("INDI",rn,db[rn])
    
    # If RN < spouse RN (including new ones)
    #    create FAM records for each spouse with ID = <HUSB rn>+<WIFE rn>
    # For No RN spouses,
    #   create INDI record for spouse
    #   if no name, name is Unknown spouse #n of <name>

    marriages = d[7]  # each is [spouse name/rn,date,place,status]
    fams = []
    seq = 0         # sequence number for this rn
    if len(marriages) == 0 and len(rdb[rn][8]) > 0:  # children, no marriage
        marriages.append(["unknown spouse of "+str(rn),'','',''])  # add unknown spouse marriage
    for m in marriages:
        seq += 1
        spouseSex = 'F' if sex == 'M' else 'F'
        spouseName = m[0]
        mdate = fixDate(m[1])        # fix date to [c]ddmmyyyy
        if mdate == None:
            mdate = m[1]
        mplace = m[2]
        mstatus = m[3]

        # find or create an RN for the spouse
        if len(m[0]) == 0:      # no name, add an "unknown spouse of rn"
            spouseName = "unknown spouse "+str(len(fams)+1)+" of "+str(rn)
            spouseRN = addNewINDI(db,spouseName,spouseSex)
        elif m[0].isdigit():            # have RN
            spouseRN = int(m[0])        
        else:                           # have NoRN name
            spouseRN = addNewINDI(db,spouseName,spouseSex)

        if rn < spouseRN:       # add family - first RN in famid is alway lower number
            famID = addNewFAM(db,fdb,rn,spouseRN)
            fdb[famID]['MARR']={'DATE':mdate,'PLAC':mplace}
            
        else:           # check and update existing family with spouse info
            famID = str(spouseRN)+'+'+str(rn)
            if famID not in fdb:
                print("***ERROR!!! RN="+str(rn),"family",famID,"not in FAM")
                continue
            if fdb[famID]['MARR']['DATE'] != mdate:
                if mdate != '':
                    if fdb[famID]['MARR']['DATE'] == '':
                        fdb[famID]['MARR']['DATE'] = mdate
                    else:
                        print("WARNING: marriage dates different for rns", 
                              spouseRN, rn,"\n\t",
                              mdate,"  |  ", fdb[famID]['MARR']['DATE'])
            if fdb[famID]['MARR']['PLAC'] != mplace:
                if mplace != '':
                    if fdb[famID]['MARR']['PLAC'] == '':
                        fdb[famID]['MARR']['PLAC'] = mplace
                    else:
                        print("WARNING: marriage places different for rns", 
                              spouseRN, rn,"\n\t",
                              mplace,"  |  ", fdb[famID]['MARR']['PLAC'])
            if debug:
                print(str(rn)+"\t"+famID+"updating family")
                
        if sex == 'M':              # for new add and old update
            statusKey = 'Hstatus'
            seqKey = 'HMarrSeq'
        else:
            statusKey = 'Wstatus'
            seqKey = 'WMarrSeq'         
        fdb[famID][statusKey] = mstatus
        fdb[famID][seqKey] = seq
        if debug:
            print("\t",fdb[famID])           

#-----------------------------------------------------------------
# MAIN PROGRAM
#-----------------------------------------------------------------
debug = False
n = [0,0,0,0,0,0,0,0,0,0,0,0]

#os.chdir("/Users/markh/Dropbox/Projects/Roots")
f4 = open("Roots.db","rb")        # read previously created roots db
rdb = pickle.load(f4,encoding='latin1')
f4.close()

##f5 = open("RootsRaw.db","rb")        # read previously created roots raw records
##raw = pickle.load(f5,encoding='latin1')
##f5.close()
##
##db = readNamelist.createINDIdb()    # create INDI database of names only
##fdb = {}                            # create FAM database & complete INDI
##for rn in range(1,len(db)+1):
##    createPass1(rn,db,fdb,rdb)
##    rn += 1
##    if rn%1000 == 0:
##        print("rn",rn)
##
##print(len(db),"INDI",len(fdb),"FAM")
##
##writeDB(db,fdb)   

db,fdb=readDB()
#createPass2(db,fdb,rdb)
checkRNChildren(db,fdb,rdb)



# convert Family.N files into Roots.db and optional RootsRaw.db
#
def preprocessRootsDB():
    #os.chdir("/Users/markh/Dropbox/Projects/Roots")
    rdb = ["first record 0"]
    raw = []
    rn = 1 
    for ext in ('1','2','3','4','5','6','7','8','9','A','B','C','D'):
        fd = open("FAMILY."+ext,"rb")
        #print("reading",ext,"rn =",rn)
        while True:
            text = fd.read(320)
            if len(text) == 0:  # end of file
                break
            raw.append(text)
            d = processRootsDB.parseRecord(rn,text)
            rdb.append(d)
            rn += 1
        fd.close()
    f4 = open("Roots.db","wb")
    pickle.dump(rdb,f4)
    f4.close()
    
    f5 = open("RootsRaw.db","wb")
    pickle.dump(raw,f5)
    f5.close()

    return rdb,raw







