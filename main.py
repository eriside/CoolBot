import nextcord
import asyncio
import json
import pytz
import aiofiles
import datetime
import humanfriendly

from nextcord.ext import commands
from datetime import datetime, timedelta
from nextcord.ext.commands import has_permissions


#def get_prefix(client, message):
#    with open('config\prefixes.json', 'r') as f:
#        prefixes = json.load(f)
#
#    return prefixes[str(message.guild.id)]








intents = nextcord.Intents.default()
intents.members = True
client = nextcord.Client()
Token = ('Toke')
client = commands.Bot(command_prefix ='?')
client.warnings = {}




@client.event
async def on_ready():
    print('Bot online {}'.format(client.user.name))
    client.loop.create_task(status_task())
    for guild in client.guilds:
        client.warnings[guild.id] = {}
        
        async with aiofiles.open(f"{guild.id}.txt", mode="a") as temp:
            pass

        async with aiofiles.open(f"{guild.id}.txt", mode="r") as file:
            lines = await file.readlines()

            for line in lines:
                data = line.split(" ")
                member_id = int(data[0])
                admin_id = int(data[1])
                reason = " ".join(data[2:]).strip("\n")

                try:
                    client.warnings[guild.id][member_id][0] += 1
                    client.warnings[guild.id][member_id][1].append((admin_id, reason))

                except KeyError:
                    client.warnings[guild.id][member_id] = [1, [(admin_id, reason)]] 
    

async def status_task():
    while True:
        await client.change_presence(activity=nextcord.Game('!help | !invite'), status=nextcord.Status.online)
        await asyncio.sleep(3)





@client.event
async def on_guild_join(guild):
    client.warnings[guild.id] = {}



@client.command()
@has_permissions(administrator=True)
async def prefix(ctx, prefix):
    with open('prefixes.json', 'r') as f:
        prefixes = json.load(f)

    prefixes[str(ctx.guild.id)] = prefix

    with open('prefixes.json', 'w') as f:
        json.dump(prefixes, f, indent=4)



@client.command()
async def invite(ctx):
    embed = nextcord.Embed()
    embed.description = "Invite me [here](https://discord.com/api/oauth2/authorize?client_id=929140744801910854&permissions=8&scope=bot%20applications.commands)."
    await ctx.send(embed=embed)

@client.command()
async def ping(ctx):
    await ctx.send(f'Pong! `{round(client.latency * 1000)}ms`')

@client.command()
@has_permissions(manage_messages=True)
async def clear(ctx, amount=5):
    await ctx.channel.purge(limit=amount+1)


@client.command()
@has_permissions(kick_members=True)
async def mute(ctx, member:nextcord.Member, time):
    time = humanfriendly.parse_timespan(time)
    await member.edit(timeout=nextcord.utils.utcnow()+timedelta(seconds=time))
    await ctx.send(f"{member} has been muted")


@client.command()
@has_permissions(kick_members=True)
async def unmute(ctx, member:nextcord.Member):
    await member.edit(timeout=None)
    await ctx.send(f"{member.member} has been unmuted")


@client.command()
@has_permissions(kick_members=True)
async def kick(ctx, member : nextcord.Member, *, reason=None):
    messageok = f"You have been **kicked** from **{ctx.guild.name} for {reason}**"
    await member.send(messageok)
    await member.kick(reason=reason)

@client.command()
@has_permissions(ban_members=True)
async def ban(ctx, member : nextcord.Member, reason=None):
    """Bans a user"""
    messageok = f"You have been **banned** from {ctx.guild.name} for **{reason}**"
    await member.send(messageok)
    await member.ban(reason=reason)


@client.command()
@has_permissions(ban_members=True)
async def unban(ctx, id: int):
    user = await client.fetch_user(id)
    await ctx.guild.unban(user)

@client.command()
async def whois(message, member: nextcord.Member, avamember : nextcord.Member=None):
    UTC= pytz.timezone('UTC')
    joined_at = member.joined_at.strftime("%b %d, %Y, %T")
    created = member.created_at.strftime("%b %d, %Y, %T")
    rlist = []
    for role in member.roles:
        if role.name != "@everyone":
            rlist.append(role.mention)
    b = ','.join(rlist)

    embed = nextcord.Embed(title='', description=member.mention,color=0xeb3b5a, timestamp=datetime.now().astimezone(tz=UTC))
    embed.set_author(name=member)
    embed.set_thumbnail(url=member.avatar_url)
    embed.add_field(name='Joined', value=joined_at, inline=True)
    embed.add_field(name='Created', value=created, inline=True)
    embed.add_field(name=f'Roles ({len(rlist)})', value=''.join([b]), inline=False)
    embed.set_footer(text='ID:' + str(member.id))
    
    await message.send(embed=embed)




@client.command()
@commands.has_permissions(administrator=True)
async def warn(ctx, member: nextcord.Member=None, *, reason=None):
    if member is None:
        return await ctx.send("The provided member could not be found or you forgot to provide one.")
        

    try:
        first_warning = False
        client.warnings[ctx.guild.id][member.id][0] += 1
        client.warnings[ctx.guild.id][member.id][1].append((ctx.author.id, reason))

    except KeyError:
        first_warning = True
        client.warnings[ctx.guild.id][member.id] = [1, [(ctx.author.id, reason)]]

    count = client.warnings[ctx.guild.id][member.id][0]

    async with aiofiles.open(f"{ctx.guild.id}.txt", mode="a") as file:
        await file.write(f"{member.id} {ctx.author.id} {reason}\n")

    embed = nextcord.Embed(title='', description=f"{member} has been warned for {reason}.")
    await ctx.send(embed=embed)
    messageok = f"You have been warned for {reason}"
    await member.send(messageok)

@client.command()
@commands.has_permissions(administrator=True)
async def warnings(ctx, member: nextcord.Member=None):
    if member is None:
        return await ctx.send("The provided member could not be found or you forgot to provide one.")
    
    embed = nextcord.Embed(title=f"Displaying Warnings for {member.name}", description="", colour=nextcord.Colour.red())
    try:
        i = 1
        for admin_id, reason in client.warnings[ctx.guild.id][member.id][1]:
            admin = ctx.guild.get_member(admin_id)
            embed.description += f"**Warning {i}** given by: <@{admin_id}> for: *'{reason}'*.\n"
            i += 1

        await ctx.send(embed=embed)

    except KeyError: # no warnings
        await ctx.send("This user has no warnings.")









@client.command()
@has_permissions(administrator=True)
async def announce( ctx, channel:nextcord.TextChannel,*, message):

        embed=nextcord.Embed(title='', description=message)
        await ctx.message.add_reaction(emoji="✅")
        ann = client.get_channel(channel.id)
        await ann.send(embed=embed)


client.run(Token) 