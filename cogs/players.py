"""
Players Cog

Handles commands related to player information and registration.
"""

import discord
from discord import app_commands
from discord.ext import commands
from typing import Optional

from services.sheets_service import get_sheets_service, Player


class PlayerRegistrationModal(discord.ui.Modal, title='Register New Player'):
    """Modal for registering a new player."""
    
    name = discord.ui.TextInput(
        label='Player Name',
        placeholder='Enter the player\'s name',
        required=True,
        max_length=50
    )
    
    commander = discord.ui.TextInput(
        label='Commander',
        placeholder='Enter the commander name',
        required=True,
        max_length=100
    )
    
    deck_name = discord.ui.TextInput(
        label='Deck Name',
        placeholder='Enter the deck name',
        required=True,
        max_length=100
    )
    
    deck_link = discord.ui.TextInput(
        label='MTG Goldfish Deck Link',
        placeholder='https://www.mtggoldfish.com/deck/...',
        required=True,
        max_length=200
    )
    
    commander_image = discord.ui.TextInput(
        label='Commander Image URL (Optional)',
        placeholder='https://...',
        required=False,
        max_length=300
    )
    
    def __init__(self, sheets_service):
        super().__init__()
        self.sheets = sheets_service
    
    async def on_submit(self, interaction: discord.Interaction):
        """Handle the modal submission."""
        player = Player(
            name=str(self.name.value),
            commander=str(self.commander.value),
            deck_name=str(self.deck_name.value),
            deck_link=str(self.deck_link.value),
            commander_image=str(self.commander_image.value) if self.commander_image.value else None
        )
        
        success = self.sheets.register_player(player)
        
        if success:
            embed = discord.Embed(
                title='✅ Player Registered!',
                color=discord.Color.green()
            )
            embed.add_field(name='Name', value=player.name, inline=True)
            embed.add_field(name='Commander', value=player.commander, inline=True)
            embed.add_field(name='Deck Name', value=player.deck_name, inline=False)
            embed.add_field(name='Deck Link', value=player.deck_link, inline=False)
            
            await interaction.response.send_message(embed=embed)
        else:
            await interaction.response.send_message(
                '❌ Failed to register player. Please try again.',
                ephemeral=True
            )


class PlayersCog(commands.Cog):
    """Cog for handling player-related commands."""
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.sheets = get_sheets_service()
    
    async def player_autocomplete(
        self,
        interaction: discord.Interaction,
        current: str
    ) -> list[app_commands.Choice[str]]:
        """Autocomplete function for player names."""
        players = self.sheets.get_player_names()
        
        return [
            app_commands.Choice(name=player, value=player)
            for player in players
            if current.lower() in player.lower()
        ][:25]  # Discord limits to 25 choices
    
    @app_commands.command(name='player', description='Get information about a player')
    @app_commands.describe(name='The name of the player')
    @app_commands.autocomplete(name=player_autocomplete)
    async def player_info(self, interaction: discord.Interaction, name: str):
        """Get information about a specific player."""
        await interaction.response.defer()
        
        try:
            player = self.sheets.get_player(name)
            
            if not player:
                await interaction.followup.send(
                    f'❌ Player "{name}" not found.',
                    ephemeral=True
                )
                return
            
            embed = discord.Embed(
                title=f'📋 Player Info: {player.name}',
                color=discord.Color.blue()
            )
            
            embed.add_field(name='Commander', value=player.commander, inline=True)
            embed.add_field(name='Deck Name', value=player.deck_name, inline=True)
            embed.add_field(name='Deck Link', value=f'[View on MTG Goldfish]({player.deck_link})', inline=False)
            
            # Get standings across all brackets
            all_standings = self.sheets.get_player_standings_all_brackets(name)
            
            if all_standings:
                standings_text = '\n'.join([
                    f'**{bracket}**: {standing.wins}W / {standing.losses}L'
                    for bracket, standing in all_standings.items()
                ])
                embed.add_field(name='Bracket Standings', value=standings_text, inline=False)
            else:
                embed.add_field(name='Bracket Standings', value='No games played yet', inline=False)
            
            # Add commander image if available
            if player.commander_image:
                embed.set_thumbnail(url=player.commander_image)
            
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            await interaction.followup.send(
                f'❌ An error occurred: {str(e)}',
                ephemeral=True
            )
    
    @app_commands.command(name='register', description='Register a new player in the league')
    async def register_player(self, interaction: discord.Interaction):
        """Register a new player."""
        modal = PlayerRegistrationModal(self.sheets)
        await interaction.response.send_modal(modal)
    
    @app_commands.command(name='players', description='List all registered players')
    async def list_players(self, interaction: discord.Interaction):
        """List all registered players."""
        await interaction.response.defer()
        
        try:
            players = self.sheets.get_all_players()
            
            if not players:
                await interaction.followup.send('No players registered yet.')
                return
            
            embed = discord.Embed(
                title='📜 Registered Players',
                color=discord.Color.blue()
            )
            
            player_list = '\n'.join([
                f'• **{p.name}** - {p.commander}'
                for p in players
            ])
            
            embed.description = player_list
            embed.set_footer(text=f'Total: {len(players)} players')
            
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            await interaction.followup.send(
                f'❌ An error occurred: {str(e)}',
                ephemeral=True
            )


async def setup(bot: commands.Bot):
    """Setup function to add this cog to the bot."""
    await bot.add_cog(PlayersCog(bot))
