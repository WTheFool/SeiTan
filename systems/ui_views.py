import discord
import math
from database.db import cursor, conn
from systems.permissions import is_admin
from systems.analytics import log
from database.db_methods import SettingsDB, SentencesDB

class AppealView(discord.ui.View):
    def __init__(self, user_id, bot):
        super().__init__(timeout=None)
        self.user_id = user_id
        self.bot = bot

    @discord.ui.button(label="Approve", style=discord.ButtonStyle.success, custom_id="approve_appeal")
    async def approve(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not is_admin(interaction.user, interaction.guild):
            return await interaction.response.send_message("Only Punishers can decide appeals.", ephemeral=True)
            
        data = SentencesDB.get_sentence(self.user_id, interaction.guild.id)
        if not data:
            return await interaction.response.send_message("This user is no longer a sinner.", ephemeral=True)
            
        days_left = data[0]
        reduction = max(1, math.floor(days_left * 0.2)) # Arbitrary 20% reduction or at least 1 day
        new_days = days_left - reduction
        
        is_global = SettingsDB.is_global_hell(interaction.guild.id)
        SentencesDB.update_days(self.user_id, interaction.guild.id, new_days, is_global)
        log(interaction.guild.id, "appeal")
        
        for child in self.children:
            child.disabled = True
            
        if new_days <= 0:
            member = interaction.guild.get_member(self.user_id)
            if member:
                sinner_role = discord.utils.get(interaction.guild.roles, name="Sinner")
                repented_role = discord.utils.get(interaction.guild.roles, name="Repented")
                
                if not repented_role:
                    repented_role = await interaction.guild.create_role(name="Repented", color=discord.Color.light_grey())
                    
                if sinner_role in member.roles:
                    await member.remove_roles(sinner_role)
                    
                await member.add_roles(repented_role)
            
            SentencesDB.delete_sentence(self.user_id, interaction.guild.id, is_global)
            await interaction.response.edit_message(content=f"**Appeal Approved by {interaction.user.mention}**\nSentence reduced to 0 days. They are free.", view=self)
        else:
            await interaction.response.edit_message(content=f"**Appeal Approved by {interaction.user.mention}**\nSentence reduced by {reduction} days.", view=self)

    @discord.ui.button(label="Reject", style=discord.ButtonStyle.secondary, custom_id="reject_appeal")
    async def reject(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not is_admin(interaction.user, interaction.guild):
            return await interaction.response.send_message("Only Punishers can decide appeals.", ephemeral=True)
            
        log(interaction.guild.id, "deny")
        
        for child in self.children:
            child.disabled = True
        await interaction.response.edit_message(content=f"**Appeal Rejected by {interaction.user.mention}**\nMercy was considered… and rejected.", view=self)

    @discord.ui.button(label="Smite", style=discord.ButtonStyle.danger, custom_id="smite_appeal")
    async def smite(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not is_admin(interaction.user, interaction.guild):
            return await interaction.response.send_message("Only Punishers can decide appeals.", ephemeral=True)
            
        data = SentencesDB.get_sentence(self.user_id, interaction.guild.id)
        if not data:
            return await interaction.response.send_message("This user is no longer a sinner.", ephemeral=True)
            
        days_left = data[0]
        addition = max(1, math.floor(days_left * 0.2)) # Arbitrary 20% addition
        new_days = days_left + addition
        
        is_global = SettingsDB.is_global_hell(interaction.guild.id)
        SentencesDB.update_days(self.user_id, interaction.guild.id, new_days, is_global)
        log(interaction.guild.id, "deny") # Log as denial/smite
        
        await self.check_titles(interaction.guild, self.user_id, new_days)
        
        for child in self.children:
            child.disabled = True
        await interaction.response.edit_message(content=f"**Appeal Smited by {interaction.user.mention}**\nSentence increased by {addition} days!", view=self)

    async def check_titles(self, guild, user_id, total_days):
        member = guild.get_member(user_id)
        if not member: return
        
        if total_days > 100000:
            role = discord.utils.get(guild.roles, name="Worse than SeiTan")
            if not role:
                role = await guild.create_role(name="Worse than SeiTan", color=discord.Color.dark_theme())
            if role not in member.roles:
                await member.add_roles(role)
        elif total_days > 10000:
            role = discord.utils.get(guild.roles, name="Irredeemable")
            if not role:
                role = await guild.create_role(name="Irredeemable", color=discord.Color.from_rgb(20, 0, 0))
            if role not in member.roles:
                await member.add_roles(role)
