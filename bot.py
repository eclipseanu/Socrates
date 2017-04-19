import discord
from discord.ext import commands
import random
import requests
import json
import sqlite3
import datetime
import configparser

#Config reader
config = configparser.ConfigParser()
config.read('config.ini')

#DB Connection setup
conn = sqlite3.connect(config['DEFAULT']['db_name'])
c = conn.cursor()

#API Key
apiKey= config['DEFAULT']['api_key']

#Discord.py bot setup
description = 'Available commands \n !mpp [country name] - Returns a list of mpps for the specified country \n !jobs [number|country name]- Returns the top jobs overall or for a specific country \n !cinfo [country name] - Returns a list of information for the specified country \n\nMore information at https://curlybear.eu/bot \nPowered by erepublik-deutschland.de'

help_attrs = dict(hidden=True)

bot = commands.Bot(command_prefix='!', description=description, pm_help=None, help_attrs=help_attrs)

#Helper functions
def is_number(s):
    try:
        float(s)
        return True
    except ValueError:
        return False

def getCountryId(country_name):
    c.execute("SELECT id FROM countries WHERE name LIKE ?", ['%'+country_name+'%'])
    data = c.fetchone()
    return int(data[0])

def getCountryName(country_id):
    c.execute("SELECT name FROM countries WHERE id == ?", [country_id])
    data = c.fetchone()
    return data[0]

def getCountryFlag(country_id):
    c.execute("SELECT flag FROM countries WHERE id == ?", [country_id])
    data = c.fetchone()
    return data[0]

def getUser(username):
    c.execute("SELECT * FROM users WHERE username LIKE ?", ['%'+username+'%'])
    data = c.fetchall()
    return data

def getUserId(id):
    c.execute("SELECT * FROM users WHERE id = ?", [id])
    data = c.fetchall()
    return data

#Commands
@bot.event
async def on_ready():
    print('Logged in as')
    print(bot.user.name)
    print(bot.user.id)
    print('------')

@bot.command()
async def getId(inCountry : str):
    await bot.say(getCountryId(inCountry))

@bot.command()
async def getName(inId : str):
    await bot.say(getCountryName(inId))

@bot.command()
async def getFlag(inId : str):
    await bot.say(getCountryFlag(inId))

@bot.command()
async def getUserT(inName : str):
    derp = getUser(inName)
    await bot.say(len(derp))
    await bot.say(derp)

@bot.command(pass_context=True)
async def mpp(ctx, inCountry : str):
    try:
        uid = getCountryId(inCountry)
        country = getCountryName(uid)
        mpptext = ''
        r = requests.get('https://api.erepublik-deutschland.de/'+ apiKey +'/countries/details/' + str(uid))
        obj = json.loads(r.text)
        mpps = obj['countries'][str(uid)]['military']['mpps']
        if not mpps:
           mpptext += '**No MPPs**'
        else:
           for mpp in mpps: 
               mpptext += getCountryFlag(mpp['country_id']) + ' **' + getCountryName(mpp['country_id']) + '** - ' + mpp['expires'][0:10] + '\n'
        em = discord.Embed(title='MPPs of ' + getCountryFlag(uid) + ' ' +  country + '', description=mpptext, colour=0x0053A9)
        await bot.send_message(ctx.message.channel, '', embed=em)
    except:
        await bot.say('Country ***' + inCountry + '*** not recognized')

@bot.command(pass_context=True)
async def cInfo(ctx, inCountry : str):
    try:
        uid = getCountryId(inCountry)
        country = getCountryName(uid)
        r = requests.get('https://api.erepublik-deutschland.de/'+ apiKey +'/countries/details/' + str(uid))
        obj = json.loads(r.text)
        poptext = '**Population:** *' + str(obj['countries'][str(uid)]['population']['total']) + '* citizens\n'
        ecotext = '**Economy:** \n**CC:** *' +  str(obj['countries'][str(uid)]['economy']['cc']) + '* \n**Gold:** *' + str(obj['countries'][str(uid)]['economy']['gold']) + '* \n**Average salary:** *' + str(obj['countries'][str(uid)]['economy']['salary_average']) + '* \n'
        admintext = '**Administration:** \n'
        if obj['countries'][str(uid)]['administration']['dictator']['id']:
            admintext += '**Dictator:** *' +obj['countries'][str(uid)]['administration']['dictator']['name'] + '* - ' + 'https://www.erepublik.com/en/citizen/profile/' + str(obj['countries'][str(uid)]['administration']['dictator']['id']) + '\n'
        if obj['countries'][str(uid)]['administration']['president']['id']:
            admintext += '**President:** *' +obj['countries'][str(uid)]['administration']['president']['name'] + '* - ' + 'https://www.erepublik.com/en/citizen/profile/' + str(obj['countries'][str(uid)]['administration']['president']['id']) + '\n'
        for minister in obj['countries'][str(uid)]['administration']['minister']:
            admintext += '**' + minister + ':** *' +obj['countries'][str(uid)]['administration']['minister'][minister]['name'] + '* - ' + 'https://www.erepublik.com/en/citizen/profile/' + str(obj['countries'][str(uid)]['administration']['minister'][minister]['id']) + '\n'
        em = discord.Embed(title='Information about '+ getCountryFlag(uid) + ' ' + country + ':', description=admintext + poptext + ecotext, colour=0x0053A9)
        await bot.send_message(ctx.message.channel, '', embed=em)
    except:
        await bot.say('Country ***' + inCountry + '*** not recognized')

@bot.command(pass_context=True)
async def jobs(ctx, inValue='3'):
    jobtext = ''

    if is_number(inValue):
        r = requests.get('https://api.erepublik-deutschland.de/'+ apiKey +'/jobmarket/bestoffers')
        obj = json.loads(r.text)
        inValue = int(inValue)
        if inValue > 5:
            inValue = 5
        for i in range(0, inValue):
            jobtext += getCountryFlag(obj['bestoffers'][i]['country_id']) + ' **' + obj['bestoffers'][i]['country_name'] + '** *' + obj['bestoffers'][i]['citizen_name'] + '*\n| Before work tax: ' + str(obj['bestoffers'][i]['salary'])+ '\n| After work tax: ' + str(obj['bestoffers'][i]['netto']) + '\n'
        em = discord.Embed(title='Best job offers:', description=jobtext, colour=0x0053A9)
        await bot.send_message(ctx.message.channel, '', embed=em)
    if type(inValue) is str:
        try:
            nbrOffers = 3
            uid = getCountryId(inValue)
            r = requests.get('https://api.erepublik-deutschland.de/'+ apiKey +'/jobmarket/countryoffers/' + str(uid))
            obj = json.loads(r.text)
            if len(obj['countryoffers']) == 0:
                jobtext += '**No offers available**'
            else:
                if len(obj['countryoffers'][str(uid)]) < 3:
                    nbrOffers = len(obj['countryoffers'][str(uid)])
                for i in range(0, nbrOffers):
                    jobtext += getCountryFlag(uid) +' **' + obj['countryoffers'][str(uid)][i]['citizen_name'] + '**\n| Before work tax: ' + str(obj['countryoffers'][str(uid)][i]['salary'])+ '\n| After work tax: ' + str(obj['countryoffers'][str(uid)][i]['netto']) + '\n'
            em = discord.Embed(title='Best job offers in ' + getCountryFlag(uid) + ' '+ inValue + ':', description=jobtext, colour=0x0053A9)
            await bot.send_message(ctx.message.channel, '', embed=em)
        except:
            await bot.say('Country ***' + inValue + '*** not recognized')

@bot.command(pass_context=True)
async def user(ctx, inValue):
    usertext = ''
    userId = ''
    if is_number(inValue):
        userId = str(int(inValue))
    else:
        userdata = getUser(inValue)
        if len(userdata) == 1:
            userId = str(int(userdata[0][1]))
        else:
            if len(userdata) > 1 and len(userdata) <= 5:
                #Display all results then await choice
                i = 1
                for citizen in userdata:
                    usertext += str(i) + ') **' + citizen[0] + '** - *' + str(int(citizen[1])) + '*\n'
                    i += 1
                em = discord.Embed(title='Please enter the number of the targeted citizen', description=usertext, colour=0x3D9900)
                await bot.send_message(ctx.message.channel, '', embed=em)
                msg = await bot.wait_for_message(author=ctx.message.author)
                if int(msg.content) >= i or int(msg.content) < 1:
                    await bot.say('Invalid choice')
                    return
                userId = str(int(userdata[int(msg.content) - 1][1]))
            else:
                if len(userdata) > 5:
                    usertext += '***' + inValue + '*** yields too many results (*'+ str(len(userdata)) +'*).\nPlease specify a more precise username'
                if len(userdata) == 0:
                    usertext += '***' + inValue + '*** doesn\'t match any known citizens.'

                em = discord.Embed(title='Citizen information', description=usertext, colour=0x3D9900)
                await bot.send_message(ctx.message.channel, '', embed=em)
                return

    r = requests.get('https://api.erepublik-deutschland.de/'+ apiKey +'/players/details/'+ userId)
    obj = json.loads(r.text)

    citizen = obj['players'][userId]

    usertext = '**Status**: ' + ('Alive' if citizen['general']['is_alive'] else 'Dead') + '\n'
    usertext += '**Date registered**: ' + citizen['general']['registered'] + '\n'
    usertext += '**ID**: ' + str(citizen['citizen_id']) + '\n'
    usertext += '**Level**: ' + str(citizen['general']['level']) + '\n'
    usertext += '**Citizenship**: ' + getCountryFlag(citizen['citizenship']['country_id']) + ' ' + citizen['citizenship']['country_name'] + '\n'
    if citizen['military_unit']['name']:
        usertext += '**Military unit**: ' + citizen['military_unit']['name'] + ' ' + 'https://www.erepublik.com/en/military/military-unit/' + str(citizen['military_unit']['id']) + '\n'
    usertext += '**Strength**: ' + str(citizen['military']['strength']) + '\n'
    usertext += '**Perception**: ' + str(citizen['military']['perception']) + '\n'
    usertext += '**Rank**: ' + str(citizen['military']['rank_name']).replace('*', '\*') + '\n'
    usertext += '**Aircraft rank**: ' + str(citizen['military']['rank_name_aircraft']).replace('*', '\*') + '\n'
    if citizen['newspaper']['name']:
        usertext += '**Newspaper**: ' + citizen['newspaper']['name'] + ' ' + 'https://www.erepublik.com/en/newspaper/' + str(citizen['newspaper']['id']) + '\n'
    usertext += '**Profile link**: https://www.erepublik.com/en/citizen/profile/' + str(citizen['citizen_id']) + '\n'

    em = discord.Embed(title='Citizen information ('+ citizen['name'] +')', description=usertext, colour=0x3D9900)
    await bot.send_message(ctx.message.channel, '', embed=em)

@bot.command()
async def ping():
    await bot.say('pong')

@bot.group(pass_context=True)
async def history(ctx):
    if ctx.invoked_subcommand is None:
        await bot.say('Invalid history command passed...')

@history.command(pass_context=True)
async def cs(ctx, inValue : str):
    usertext = ''
    userId = ''
    userName = ''
    if is_number(inValue):
        userId = str(int(inValue))
        userName = (getUserId(userId))[0][0]
    else:
        userdata = getUser(inValue)
        if len(userdata) == 1:
            userId = str(int(userdata[0][1]))
            userName = userdata[0][0]
        else:
            if len(userdata) > 1 and len(userdata) <= 5:
                i = 1
                for citizen in userdata:
                    usertext += str(i) + ') **' + citizen[0] + '** - *' + str(int(citizen[1])) + '*\n'
                    i += 1
                em = discord.Embed(title='Please enter the number of the targeted citizen', description=usertext, colour=0x3D9900)
                await bot.send_message(ctx.message.channel, '', embed=em)
                msg = await bot.wait_for_message(author=ctx.message.author)
                if int(msg.content) >= i or int(msg.content) < 1:
                    await bot.say('Invalid choice')
                    return
                userId = str(int(userdata[int(msg.content) - 1][1]))
                userName = userdata[int(msg.content) - 1][0]
            else:
                if len(userdata) > 5:
                    usertext += '***' + inValue + '*** yields too many results (*'+ str(len(userdata)) +'*).\nPlease specify a more precise username'
                if len(userdata) == 0:
                    usertext += '***' + inValue + '*** doesn\'t match any known citizens.'

                em = discord.Embed(title='Citizen information', description=usertext, colour=0x3D9900)
                await bot.send_message(ctx.message.channel, '', embed=em)
                return

    r = requests.get('https://api.erepublik-deutschland.de/'+ apiKey +'/players/history/cs/'+ userId)
    obj = json.loads(r.text)
    usertext = ''
    hists = obj['history'][userId]['cs']
    if len(hists) > 0:
        hists = sorted(hists, key=lambda x: x['added'])
        for hist in hists:
            usertext += getCountryFlag(hist['country_id_from']) + ' ***' + hist['country_name_from'] + '*** to ' + getCountryFlag(hist['country_id_to']) + ' ***' + hist['country_name_to'] + '*** on ' + hist['added'] + '\n'
    else:
        usertext = 'No history to display.'
    em = discord.Embed(title='Citizen history ('+ userName +')', description=usertext, colour=0x3D9900)
    await bot.send_message(ctx.message.channel, '', embed=em)

bot.run(config['DEFAULT']['bot_token'])