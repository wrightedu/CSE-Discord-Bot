import json
from datetime import datetime
from time import time

import discord
from discord.ext import commands, tasks


class Invites(commands.Cog):
    def __init__(self, bot, savepath='invites.json'):
        self.bot = bot
        self.savepath = savepath
        self.invites = loadInvites(savepath)
        self.hasBeenRemoteSynced = False
        self.startTime = time()
        self.syncUseCounts.start()

    # Task to update the local use counts on startup
    @tasks.loop(seconds=1)
    async def syncUseCounts(self):
        if not self.hasBeenRemoteSynced:
            if time() > self.startTime + 5:
                # Get a member object so I can get the invite uses (self.bot.fetch_invite() doesn't work)
                memberobj = None
                for member in self.bot.get_all_members():
                    memberobj = member
                    break

                # Iterate through member invites and update the local use counts if they share a url with a local saved url
                memberInvites = await member.guild.invites()
                for invite in memberInvites:
                    if invite.url in self.invites.keys():
                        self.invites[invite.url]['uses'] = invite.uses
                await log('Invite use counters synced')
                self.hasBeenRemoteSynced = True

    ###### ================================== ######
    ######               Events               ######
    ###### ================================== ######
    @commands.Cog.listener()
    async def on_member_join(self, member):
        invites = await member.guild.invites()

        for invite in invites:
            if invite.url in self.invites.keys():
                savedInvite = self.invites[invite.url]
                if invite.uses > savedInvite['uses']:

                    channelName = savedInvite['channelName']
                    roleName = savedInvite['roleName']
                    roleID = savedInvite['roleID']
                    savedInvite['uses'] = invite.uses
                    purpose = savedInvite['purpose']

                    role = discord.utils.get(member.guild.roles, id=roleID)
                    await member.add_roles(role)

                    await log(f'{purpose} {member} has joined in {channelName} and was given role {roleName}')

                    # If new member is a prospective student, automatically say hello
                    channel = discord.Client().get_channel(702895094881058896)
                    await channel.send(f'Hello, {member.mention}')

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        await log(f'{member} has left the server')


def setup(bot):
    bot.add_cog(Invites(bot))


async def log(string, timestamp=True):
    if timestamp:
        print(f'[{str(datetime.now())[:-7]}]', end=' ')
    print(string)


def loadInvites(filepath):
    try:
        with open(filepath, 'r') as f:
            invites = json.loads(f.read())
            return invites
    except Exception as e:
        print('Loading invites failed')
        print(e)
        return {}


async def log(string, timestamp=True):
    if timestamp:
        print(f'[{str(datetime.now())[:-7]}]', end=' ')
    print(string)
