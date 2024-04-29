import os
import time
import asyncio
import random
import aiofiles

all = {}

pipeRoot = '/home/moderator/pipes/'
logName = ''
mLogName = ''
conns = {}
allowed = {}
logChat = 0
currentTime = 0

readVulnerability = 0
readVulnerability_2 = 0
imposterMode = 1
isSilent = 1

voting = False
chatting = False

def setVars(passedReadVulnerability, passedReadVulnerability_2,passedImposterMode, publicLogName, moderatorLogName):
    global readVulnerability, readVulnerability_2,imposterMode, logName, mLogName
    readVulnerability = int(passedReadVulnerability)
    readVulnerability_2 = int(passedReadVulnerability_2)
    imposterMode = int(passedImposterMode)
    logName = publicLogName
    mLogName = moderatorLogName

def complement(x, y):
    z = {}
    for element in list(y.keys()):
        if element not in list(x.keys()): z[element] = y[element]
    return z

def skip():
    global currentTime, deathspeech, deadGuy, voters, targets
    currentTime = 0
    deathspeech = 0
    deadGuy = ""
    voters = {}
    targets = {}

async def sleep(duration):
    await asyncio.sleep(duration)

def setLogChat(n):
    global logChat
    logChat = n

def obscure():
    pass

def allow(players):
    global allowed
    allowed = players

async def broadcast(msg, players):
    global logChat
    await log(msg, 1, logChat, 1)

    await asyncio.sleep(.1)

    for player in list(players.keys()):
        try:
            await send(msg, players[player][1])
        except Exception as p: pass

async def send(msg, writer):
    try:
        writer.write(msg.encode())
        await writer.drain()
    except Exception as p:
        print('send error:%s'%p)


async def log(msg, printBool, publicLogBool, moderatorLogBool):
    global logName, mLogName

    if printBool:
        print(msg)

    msg = '(%s) - %s\n'%(str(int(time.time())), msg)
    if publicLogBool:
        async with aiofiles.open(logName, 'a') as f:
            await f.write(msg)
    if moderatorLogBool:
        async with aiofiles.open(mLogName, 'a') as g:
            await g.write(msg)


deathspeech = 0
deadGuy = ""

def modPlayers(player, players):
    newPlayers = {}
    for p in list(players.keys()):
        if p != player:
            newPlayers[p] = players[p]
    return newPlayers

votetime = 0
voteAllowDict = {'w':0, 'W':0, 't':0}
votes = {}
votesReceived = 0
voters = {}
targets = []
character = ""

voter_targets = {}

async def poll(passedVoters, duration, passedValidTargets, passedCharacter, everyone, isUnanimous, passedIsSilent):
    global votes, voteAllowDict, allowed, votesReceived, logChat, votetime, voters, targets, character, isSilent, voter_targets, voting

    voting = True
    votetime = 1
    voters = passedVoters
    votesReceived = 0
    votes = {}
    targets = passedValidTargets
    character = passedCharacter
    isSilent = passedIsSilent

    voter_targets = {}

    await asyncio.sleep(duration+1)
    await log(str(votes), 1, logChat, 1)

    voting = False
    results = []
    mode = 0
    for v in list(votes.keys()):
        if votes[v] > mode:
            mode = votes[v]
            results = [v]
        elif votes[v] == mode:
            results.append(v)

    #this var signifies the class of result
    #0 - results[0]=victim; 1 - vote not unan; 2 - vote is tie
    resultType = 0

    if int(isUnanimous) and mode != len(passedVoters): #the voteCount of the winner is not equal the number of voters
        resultType = 1
    elif len(results) > 1 or len(results) == 0:#tie or nonvote
        resultType = 2

    validTargets = []
    votetime = 0
    voters = {}
    #voter_targets = {}

    return results, resultType

async def vote(voter, target):
    global votes, votesReceived, voters, character, isSilent, voter_targets

    # Code Updated on 7/20 by Tim
    if voter_targets.get(voter, None) == None:  # Added line

        if target in targets:
            try: votes[target] += 1  # changed from += 1 to just 1
            except: votes[target] = 1
            #message[0] is sent to who[0]; message[1] sent to who[1]; etc.
            messages = []
            who = []

            await log(voter + " voted for " + target, 1, 0, 1)

            if character == "witch":
                messages.append("Witch voted")
                who.append(all)
            elif character == "wolf":
                if isSilent: messages.append('%s voted.'%voter)
                else: messages.append('%s voted for %s'%(voter, target))
                #messages.append("Wolf vote received.")
                who.append(voters)

                messages.append("Wolf vote received.")
                comp = complement(voters, all)
                who.append(comp)
                #who.append(complement(voters,all))
            else:#townsperson vote
                if isSilent: messages.append('%s voted.'%voter)
                else: messages.append('%s voted for %s'%(voter, target))
                who.append(all)

            for i in range(len(messages)):
                await broadcast(messages[i], who[i])


            votesReceived += 1
            voter_targets[voter] = target  

            if votesReceived == len(voters): skip()

        else:
            #vote_targets[voter] = None  # Added by Tim
            await send('invalid vote: %s'%target, voters[voter][1])

    # Added by Tim    
    else:
        await send('You already voted: %s'%target, voters[voter][1])

async def spawnDeathSpeech(player, endtime):
    global deathspeech, deadGuy
    deathspeech = 1
    deadGuy = player

    await sleep(endtime)

    deathspeech = 0
    deadGuy = ""
