import asyncio
import os
import random
import communication as c

listening = True
handlingConnections = True

i = {}
inputVars = open('config', 'r').read().split('\n')
for var in inputVars:
    var = var.strip('\n').split('=')
    key = var[0]
    try:#if a line doesn't have an = sign
        value = var[1]
    except:
        continue
    i[key] = value
logFile = ''

#time parameters
timeTillStart = int(i['timeTillStart'])
wolftalktime = int(i['wolfTalkTime'])
wolfvotetime = int(i['wolfVoteTime'])
townvotetime = int(i['townVoteTime'])
towntalktime = int(i['townTalkTime'])
witchvotetime = int(i['witchVoteTime'])
deathspeechtime = int(i['deathSpeechTime'])

test = int(i['test'])
giveDeathSpeech = int(i['deathSpeech'])
numWolves = int(i['numWolves'])

#moderator assignment global vars
wolfChoose = int(i['wolfChoose'])
moderatorAssignment = 0
moderatorAssignmentContinue = 0
moderatorAssignmentList = []

#group people by roles
all = {}
wolves = {}
townspeople = {}
witch = {}

potions = [int(i['kill']), int(i['heal'])]#[kill,heal]

round_no = 1


async def removePlayer(player):
    global all, wolves, witch
    isTownsperson = 1

    newAll = {}
    for p in list(all.keys()):
        if player != p: newAll[p] = all[p]
    newWolves = {}
    for p in list(wolves.keys()):
        if player != p : newWolves[p] = wolves[p]
        await c.log('%s-wolf killed.'%p, 1, 0, 1)
        isTownsperson = 0
    if player in list(witch.keys()):
        await c.log('%s-witch killed'%player, 1, 0, 1)
        witch = {}
        isTownsperson = 0
    if isTownsperson:
        pass
        await c.log('%s-townsperson killed'%player, 1, 0, 1)
    c.setLogChat(1)
    if giveDeathSpeech:
        await c.broadcast('These are %ss last words.'%player, all)
        await c.send("Share your parting words.", all[player][1])
        await c.spawnDeathSpeech(player, deathspeechtime)

    c.setLogChat(0)

    # Commented code to close terminal to fix bug of game crashing when 
    # a player is removed from the game. 
    #c.send('close',all[player][1]) 

    await c.send("YOU ARE DEAD. You will continue getting game updates, Please *DO NOT* close this terminal", all[player][1])
    all = newAll
    wolves = newWolves
    if len(wolves) <= 1: wolftalktime = 0

async def assign():
    global all, wolves, witch, moderatorAssignment, moderatorAssignmentContinue, moderatorAssignmentList, moderatorAssignmentChoices
    numPlayers = len(list(all.keys()))

    if not wolfChoose: #randomly assign roles
        config = ['W']
        for i in range(numWolves): config.append('w')
        for i in range(numPlayers-numWolves-1): config.append('t')

    #randomize roles
        random.shuffle(config)

    #assign roles and inform players
        for i in range(len(list(all.keys()))):
            player = list(all.keys())[i]

            if config[i] == 'w':
                wolves[player] = all[player]
                role = 'wolf'
            elif config[i] == 'W':
                witch[player] = all[player]
                townspeople[player] = all[player]
                role = 'witch'
            else:
                townspeople[player] = all[player]
                role = 'townsperson'
            await c.send('~~~~~ YOU ARE A %s ~~~~~'%role, all[player][1])
    else: #moderator chooses roles
        moderatorAssignment = 1
        print('\nModerator Assignment:')
        moderatorAssignmentChoices = list(all.keys())
        print('Choose wolves from %s. enter "done" when finished.'%str(sorted(moderatorAssignmentChoices)))
        moderatorAssignmentContinue = 1
        while moderatorAssignmentContinue == 1:
            await asyncio.sleep(1)
        wolfList = moderatorAssignmentList
        moderatorAssignmentList = []

        moderatorAssignmentChoices = []
        for p in list(all.keys()):
            if p not in wolfList: moderatorAssignmentChoices.append(p)
        print('Choose witch from %s.'%str(sorted(moderatorAssignmentChoices)))
        moderatorAssignmentContinue = 1
        while moderatorAssignmentContinue == 1:
            if len(moderatorAssignmentList) == 1:
                if moderatorAssignmentList[0] in wolfList:
                    moderatorAssignmentList = []
                else: break
            else: await asyncio.sleep(0.1)
        witchList = moderatorAssignmentList
        moderatorAssignment = 0

        for player in list(all.keys()):
            if player in witchList:
                witch[player] = all[player]
                role = 'witch'
            elif player in wolfList:
                wolves[player] = all[player]
                role = 'wolf'
            else: #player is a townsperson
                townspeople[player] = all[player]
                role = 'townsperson'
            message = '~~~~~ YOU ARE A %s ~~~~~'%role
            await c.send(message, all[player][1])


async def client_loop(reader, writer):
    global all, voting, chatting

    while listening:
        data = await reader.read(100)
        message = data.decode()
        player = message.split(':')[0]
        message = message.split(':')[1]

        if message == 'connect':
            if handlingConnections:
                all[player] = [reader,writer]
                return_message = f'Hello, {player}.  You are connected.  Please wait for the game to start.'
                writer.write(return_message.encode())
                await writer.drain()
            else:
                return_message = 'Game already started.  Please wait for next game.'
                writer.write(return_message.encode())
                writer.write('close'.encode())
                await writer.drain()
        else:
            if c.deathspeech and player == c.deadGuy:
                await c.broadcast('%s-%s'%(player, message), c.modPlayers(player, all))
            elif c.voting and player in list(c.voters.keys()):
                await c.vote(player, message)
            elif player in c.allowed:
                await c.broadcast('%s-%s'%(player, message), c.modPlayers(player, c.allowed))

async def close():
    global all
    for player in list(all.keys()):
        all[player][1].write('close'.encode())
        await all[player][1].drain()

async def standardTurn():
    global all, witch, potions, towntalktime,wolftalktime
    wolfkill = 0
    witchkill = 0
    try:
        await c.broadcast("Night falls and the town sleeps.  Everyone close your eyes", all)
        await c.log('Night', 0, 1, 0)

    #**************WEREWOLVES************************
        if len(wolves) < 2: wolftalktime = 0
        await c.broadcast("Werewolves, open your eyes.", c.complement(wolves, all))
        await c.broadcast('Werewolves, %s, you must choose a victim.  You have %d seconds to discuss.  Possible victims are %s'%(str(list(wolves.keys())), wolftalktime, str(sorted(all.keys()))), wolves)
        await c.log('Werewolves debate', 0, 1, 0)
        c.allow(wolves)
        await c.sleep(wolftalktime)
        await c.broadcast("Werewolves, vote.", c.complement(wolves, all))
        await c.broadcast('Werewolves, you must vote on a victim to eat.  You have %d seconds to vote.  Valid votes are %s.'%(wolfvotetime, str(sorted(all.keys()))),wolves)
        await c.log('Werewolves vote', 0, 1, 0)
        wolfvote,voteType = await c.poll(wolves, wolfvotetime, list(all.keys()), 'wolf', all, i['wolfUnanimous'], i['wolfSilentVote'])
        await c.broadcast('Werewolves, go to sleep.', c.complement(wolves, all))

        if voteType == 1:
            await c.broadcast('Vote not unanimous, nobody eaten.', wolves)
            await c.log('Werewolves not unanimous', 0, 1, 0)
        elif voteType == 2:
            await c.broadcast('Tie', wolves)
            await c.log('Werewolves vote tie', 0, 1, 0)
        elif voteType == 0:
            msg = "Werewolves, you selected to eat %s"%str(wolfvote[0])
            wolfkill = 1
            await c.broadcast(msg, wolves)
            await c.log('Werewolves selected %s'%str(wolfvote[0]), 0, 1, 0)
    #**********END WEREWOLVES************************


    #**************WITCH************************
    #construct the witch's options
        if len(witch) > 0 and (potions[0] or potions[1]):
            await c.broadcast('Witch, open your eyes.', c.complement(witch, all))
            await c.log('Witch vote', 0, 1, 0)
            witchPlayer = witch[list(witch.keys())[0]]

            if wolfkill:
                validKills = []
                for p in all:
                    if p != wolfvote[0]:
                        validKills.append(p)
                validKills = sorted(validKills)
                if potions[0] and potions[1]:
                    witchmoves = validKills + ['Heal', 'Pass']
                elif potions[0]:
                    witchmoves = validKills + ['Pass']
                else:
                    witchmoves = ['Heal', 'Pass']
                await c.send('Witch, wake up.  The wolves killed %s.  Valid votes are %s.'%(str(wolfvote), str(witchmoves)), witchPlayer[1])
                await c.broadcast('The witch is now voting...', all)
            else:
                if potions[0]:
                    witchmoves = sorted(all.keys()) + ['Pass']
                else:
                    witchmoves = ['Pass']
                await c.send('Witch, the wolves didn\'t feed tonight.  Valid votes are %s'%str(witchmoves),witchPlayer[1])
                await c.broadcast('The witch is now voting...', all)

    #witch voting
            if len(witchmoves) > 1:
                witchVote,voteType = await c.poll(witch, witchvotetime, witchmoves, 'witch', all, 0, 0)
            else:
                witchVote = []
                voteType = 9999

            if witchVote == [] or witchVote[0] == 'Pass' or voteType != 0:
                await c.log('Witch passed', 1, 1, 1)
                await c.broadcast('Witch, close your eyes', all)
            elif witchVote[0] == 'Heal':
                await c.send('The Witch healed you!', all[wolfvote[0]][1])
                await c.log('The Witch healed %s!'%wolfvote[0], 0, 0, 1)
                wolfkill = 0
                potions[1] -= 1
                await c.broadcast('The witch used a health potion! %d heal[s] remaining.'%potions[1], all)
        #await c.broadcast('The witch used a health potion! '+str(potions[1])+' heal[s] remaining.',all)
            else:
                witchkill = 1
                potions[0] -= 1
                await c.broadcast('Witch, close your eyes', all)
        else:
            await c.broadcast('Witch, open your eyes.', all)
            await c.sleep(random.random() * 20)
            await c.broadcast('Witch, close your eyes', all)
    #**************END WITCH************************
    #**************START TOWN***********************
        if wolfkill:
            await c.broadcast('The werewolves ate %s!'%wolfvote[0], all)
            await c.log('Werewolves killed %s'%wolfvote[0], 0, 1, 0)
            await removePlayer(wolfvote[0])

        if len(wolves) == 0 or len(all) == len(wolves):
            return 1

        if witchkill:
            await c.broadcast('The Witch poisoned %s!  %d poison[s] remaining.'%(witchVote[0], potions[0]), all)
            await c.log('Witch poisoned %s'%witchVote[0], 0, 1, 0)
            await removePlayer(witchVote[0])

        if len(all) - len(wolves) == 0 or len(wolves) == 0:
            return 1


        c.allow(all)
        c.setLogChat(1)
        if len(all) == 2: towntalktime = 0
        await c.broadcast('It is day.  Everyone, %s, open your eyes.  You will have %d seconds to discuss who the werewolves are.'%(str(sorted(all.keys())), towntalktime), all)
        await c.log('Day-townspeople debate', 0, 1, 0)
        await c.sleep(towntalktime)
        c.allow({})
        await c.log('Townspeople vote', 0, 1, 0)
        await c.broadcast('Townspeople, you have %d seconds to cast your votes on who to hang. Valid votes are %s'%(townvotetime, str(sorted(all.keys()))), all)

        killedPlayer, voteType = await c.poll(all, townvotetime, list(all.keys()), 'town', all, i['townUnanimous'], i['townSilentVote'])
        if voteType == 2:
            msg = 'The vote resulted in a tie between players %s, so nobody dies today.'%killedPlayer
            await c.broadcast(msg, all)
            c.log('Townspeople vote tie', 0, 1, 0)
        elif voteType == 1:
            await c.broadcast('The vote was not unanimous', all)
            await c.log('Townspeople vote not unanimous', 0, 1, 0)
        else:
            await c.broadcast('The town voted to hang %s!'%killedPlayer[0], all)
            await c.log('Townspeople killed %s'%str(killedPlayer[0]), 0, 1, 0)
            await removePlayer(killedPlayer[0])

        c.setLogChat(0)
    #******************END TOWN*******************
        return 1
    except Exception as error:
        await c.log('STANDARDTURNERROR:%s'%str(error), 1, 0, 1)
        return 0

async def main():
    global isHandlingConnections, round_no, all, moderatorLogName, winner, gameNumber

    if test:
        publicLogName = 'log/dummy.log'
        moderatorLogName = 'log/dummy-m.log'
        os.chmod(moderatorLogName, 0o700)
        gameNumber = 9999
    else:
        nextround = open('log/nextround', 'r')
        gameNumber = int(nextround.readline().strip('\n'))
        nextround.close()
        nextround = open('log/nextround', 'w')
        nextround.write(str(gameNumber + 1))
        nextround.close()
        msg = 'Game %d starts in %d seconds.'%(gameNumber, timeTillStart)
        #msg='Game '+str(next)+' starts in '+str(timeTillStart)+' seconds.'
        os.system('echo "%s" | wall'%msg)
        publicLogName='log/%d.log'%gameNumber
        moderatorLogName='log/%dm.log'%gameNumber

        if i['moderatorLogMode'] == 1:
            os.system('touch ' + moderatorLogName)
            os.system('chmod 700 ' + moderatorLogName)
        else:
            os.system('cp log/template ' + moderatorLogName)

    #pass the necessary input variables into the communication script
    c.setVars(i['readVulnerability'], i['readVulnerability2'], i['imposterMode'], publicLogName, moderatorLogName)

    await c.log('GAME: %d'%gameNumber, 1, 1, 1)
    await c.log('\nmoderator listener thread started', 1, 0, 1)

    server = await asyncio.start_server(
        client_loop, '127.0.0.1', 8888)

    addrs = ', '.join(str(sock.getsockname()) for sock in server.sockets)
    print(f'Serving on {addrs}')

    async with server:
        await asyncio.sleep(10)
        isHandlingConnections = False
        await assign()
        await c.broadcast('There are ' + str(len(wolves)) + ' wolves, and ' + str(len(all) - len(wolves)) + ' townspeople.', all)
        c.allow({})

        while len(wolves) != 0 and len(wolves) < len(all):
            await c.log('\n\n', 1, 1, 1)
            await c.broadcast('*' * 50, all)
            await c.broadcast('*' * 21 + 'ROUND ' + str(round_no) + '*' * 22, all)
            await c.broadcast('*' * 15 + str(len(all)) + ' players remain.' + '*' * 18, all)
            await c.broadcast('*' * 50, all)
            await c.log('Round ' + str(round_no), 0, 1, 0)
            await c.log('Townspeople: ' + str(list(all.keys())), 1, 1, 1)
            await c.log('Werewolves: ' + str(list(wolves.keys())), 1, 0, 1)
            await c.log('Witch: ' + str(list(witch.keys())), 1, 0, 1)
            round_no += 1
            await standardTurn()

        if len(wolves) == 0: winner = 'Townspeople win'
        elif len(wolves) == len(all): winner = 'Werewolves win'
        await c.log('\n%s'%winner, 0, 1, 0)
        await c.broadcast(winner, all)
        await c.broadcast('close', all)


        await c.log('End', 1, 1, 1)
        if not test: os.chmod('log/%dm.log'%gameNumber, 0o744)
        if not test: os.system('echo "Game %d is over.  %s.  Please reconnect your client to play again." | wall'%(gameNumber, winner))
        await close()
        exit()

asyncio.run(main())