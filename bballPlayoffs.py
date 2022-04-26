

import requests
import pandas as pd
import re
import math

# Get table data from website
playoffRound = 1
def getTable(name,subType):
    html = requests.get(name).content
    dfList = pd.read_html(html)
    if subType == 1:
        trTable = dfList[-1]
    elif subType == 2:
        trTable = pd.concat([dfList[3],dfList[4]])
    return trTable

statFoxTable = getTable('https://www.statfox.com/nba/gamematchup.asp',1)

# First system -- home underdogs with low ATS
# Extract relevant info from table
def refinedTable(oldTable):
    newTable = []
    tempATS = []
    tempSU = []
    a = 0
    count = 0
    for i in range(2,len(oldTable)-1,6):
        newTable.append(oldTable.iloc[i:i+3,:])
        b = 1
        
        # Convert ATS to ratio
        for t in range(2):
            tempATS.append(newTable[a].iloc[b,5].split('-'))
            tempSU.append(newTable[a].iloc[b,4].split('-'))
            newTable[a].iloc[b,5] = int(tempATS[count][0]) / (int(tempATS[count][0])+int(tempATS[count][1])+int(tempATS[count][2]))*100
            newTable[a].iloc[b,4] = int(tempSU[count][0]) / (int(tempSU[count][0])+int(tempSU[count][1]))*100
            b = 2
            count = count + 1
        a = a + 1
    return newTable
newFoxTable = refinedTable(statFoxTable)

# Find games that match the first system
def sys1(newTable):
    system1 = []
    teamSU = []
    for k in range(len(newTable)):
        if newTable[k].iloc[2,5] < 51 and newTable[k].iloc[1,5] > 52:
            system1.append(newTable[k].iloc[2,0])
        if newTable[k].iloc[2,4] > 64:
            teamSU.append(newTable[k].iloc[2,0])
    return system1,teamSU
system1,teamWinPct = sys1(newFoxTable)
        

# Second system -- 'New' road teams (first round only)
lastYearTeams = getTable('https://en.wikipedia.org/wiki/2021_NBA_playoffs',2)

def lyTeams(lastYearTeams):
    system2 = []
    newLastYearsTeams = []
    newLYteams = []
    lastYearTeams.iloc[:,1] = lastYearTeams.iloc[:,1].str.upper()
    lastYearTeams.iloc[:,1] = lastYearTeams.iloc[:,1].str.split()
    lastYearTeams.index = range(16)
    
    for i in range(len(newFoxTable)):
        awayTeam = newFoxTable[i].iloc[1,0].split(':')
        awayTeam[1] = awayTeam[1].lstrip()
        homeTeam = newFoxTable[i].iloc[2,0].split(':')
        homeTeam[1] = homeTeam[1].lstrip()
        
        if i == 0:
            for k in lastYearTeams['Team']:
                newLastYearsTeams.append(lastYearTeams[k])
    
            for m in range(16):
                if len(newLastYearsTeams[0].iloc[m][0]) > 2:
                        newLastYearsTeams[0].iloc[m][0] = [newLastYearsTeams[0].iloc[m][0][0] + ' ' + str(newLastYearsTeams[0].iloc[m][0][1])]
                newLYteams.append(newLastYearsTeams[0].iloc[m][0][0])
        if awayTeam[1] not in newLYteams and homeTeam[1] in newLYteams:
                system2.append(awayTeam[1])
    return system2
if playoffRound < 2:
    system2 = lyTeams(lastYearTeams)
        
# Third system -- fade the trendy underdog
pctBetsTable = getTable('https://www.actionnetwork.com/nba/public-betting',1)

def underdogs(pctBetsTable,newFoxTable):
    teamNames = []
    if math.isnan(pctBetsTable.iloc[1,0]):
        for m in pctBetsTable.iloc[0::3,0]:
            brokeString = re.findall('[A-Z][^A-Z]*', m)
            for word in brokeString:
                if word.isalpha() and len(word) > 3:
                    teamNames.append(word)
    else:
        for m in pctBetsTable['Scheduled']:
            brokeString = re.findall('[A-Z][^A-Z]*', m)
            for word in brokeString:
                if word.isalpha() and len(word) > 3:
                    teamNames.append(word)
    
    tempPctBets = []
    pctBets = []
    for i in pctBetsTable['% of Bets']:
        stringSplit = i.split('w')
        tempPctBets.append(stringSplit[1].split('%') + stringSplit[2].split('%'))
    for k in range(len(tempPctBets)):
        pctBets.append([int(tempPctBets[k][0]),int(tempPctBets[k][2])])
    
    count = 4
    favTeam = []
    for j in newFoxTable:
        if j.loc[count,1].find('+'):
            favTeam.append([j.loc[count,0],0])
        else:
            favTeam.append([j.loc[count-1,0],1])
        count = count + 6
        
    system3 = []
    for ii in range(len(favTeam)):
        if favTeam[ii][1] == 0 and pctBets[ii][1] < 40:
            system3.append(favTeam[ii][0])
        elif favTeam[ii][1] == 1 and pctBets[ii][0] < 40:
            system3.append(favTeam[ii][0])
    return system3
system3 = underdogs(pctBetsTable,newFoxTable)

# Fourth system -- home bounceback
# http://www.playoffstatus.com/nba/nbaplayoffschedule.html
dfOldScores = pd.read_csv(r"C:\Users\Alex\Documents\dataAnalysis\sports\priorScores.csv", encoding= 'unicode_escape')
dfUpcoming = pd.read_csv(r"C:\Users\Alex\Documents\dataAnalysis\sports\upcomingGames.csv", encoding= 'unicode_escape')

def comebackWin(dfOldScores,dfUpcoming):
    def newTable(dfOldScores,subType):
        newTable = []
        for i in range(len(dfOldScores)):
            dfOldScores.iloc[i,2] = dfOldScores.iloc[i,2].split()
            dfOldScores.iloc[i,2] = dfOldScores.iloc[i,2][0]
            if subType == 1:
                newTable.append(dfOldScores.iloc[i,1].split('?'))
            
                for k in range(len(newTable[i])):
                    newTable[i][k] = int(newTable[i][k])
        if subType == 1:
            n = dfOldScores.columns[1]
            dfOldScores.drop(n, axis = 1, inplace = True)
            dfOldScores[n] = newTable
            
            test = []
            test1 = []
            for m in range(len(dfOldScores)):
                test.append(dfOldScores.iloc[m,2][0] - dfOldScores.iloc[m,2][1])
                test1.append(dfOldScores.iloc[m,2][1] - dfOldScores.iloc[m,2][0])
            dfOldScores['team1 outcome'] = test
            dfOldScores['team2 outcome'] = test1
        return dfOldScores
    
    dfOldScores = newTable(dfOldScores,1)
    dfUpcoming = newTable(dfUpcoming,2)
    
    teamApplies = []
    for j in range(len(dfUpcoming)):
        
        tempTeam = dfOldScores[dfUpcoming.iloc[j,2]==dfOldScores['team1']]
        team2grab = 0
        outcome2grab = 3
        if tempTeam.empty:
            tempTeam = dfOldScores[dfUpcoming.iloc[j,2]==dfOldScores['team2']]
            team2grab = 1
            outcome2grab = 4
        if tempTeam.iloc[0,outcome2grab] <= -10:
            teamApplies.append(tempTeam.iloc[0,team2grab])
    return teamApplies
teamsBeatBy10 = comebackWin(dfOldScores,dfUpcoming)
system4 = [teamsBeatBy10,teamWinPct]

# Fifth system -- unders
def sys5(dfUpcoming):
    system5unders = []
    for i in range(len(dfUpcoming)):
        dfUpcoming.iloc[i,3] = dfUpcoming.iloc[i,3].split()
        if int(dfUpcoming.iloc[i,3][0][0])==0 and int(dfUpcoming.iloc[i,3][0][1]) < 5:
            system5unders.append(dfUpcoming.iloc[i,0])
    return system5unders

if playoffRound < 3:
    system5unders = sys5(dfUpcoming)
    