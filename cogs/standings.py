"""
Standings Cog

Handles commands related to league standings.
"""

import discord
from discord import app_commands
from discord.ext import commands

from services.sheets_service import get_sheets_service


class StandingsCog(commands.Cog):
    """Cog for handling standings-related commands."""
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.sheets = get_sheets_service()
    
    @app_commands.command(name='standings', description='Get the current standings for a bracket')
    @app_commands.describe(bracket='The budget bracket to get standings for')
    @app_commands.choices(bracket=[
        app_commands.Choice(name='$60 Bracket', value='$60s'),
        app_commands.Choice(name='$70 Bracket', value='$70s'),
        app_commands.Choice(name='$80 Bracket', value='$80s'),
        app_commands.Choice(name='$90 Bracket', value='$90s'),
        app_commands.Choice(name='$100 Bracket', value='$100s'),
        app_commands.Choice(name='All Brackets', value='all'),
    ])
    async def standings(self, interaction: discord.Interaction, bracket: app_commands.Choice[str]):
        """Get standings for a specific bracket or all brackets."""
        await interaction.response.defer()
        
        try:
            if bracket.value == 'all':
                # Get standings for all brackets
                embed = discord.Embed(
                    title='🏆 League Standings - All Brackets',
                    color=discord.Color.gold()
                )
                
                for b in self.sheets.get_available_brackets():
                    standings = self.sheets.get_standings_for_bracket(b)
                    
                    if standings:
                        standings_text = '\n'.join([
                            f'{i+1}. **{s.name}** - {s.wins}W / {s.losses}L'
                            for i, s in enumerate(standings[:5])  # Top 5 per bracket
                        ])
                    else:
                        standings_text = 'No games recorded yet'
                    
                    embed.add_field(
                        name=f'{b} Bracket',
                        value=standings_text,
                        inline=False
                    )
            else:
                # Get standings for specific bracket
                standings = self.sheets.get_standings_for_bracket(bracket.value)
                
                embed = discord.Embed(
                    title=f'🏆 {bracket.name} Standings',
                    color=discord.Color.gold()
                )
                
                if standings:
                    standings_text = '\n'.join([
                        f'{i+1}. **{s.name}** - {s.wins} wins, {s.losses} losses'
                        for i, s in enumerate(standings)
                    ])
                    embed.description = standings_text
                else:
                    embed.description = 'No games recorded yet for this bracket.'
            
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            await interaction.followup.send(
                f'❌ An error occurred while fetching standings: {str(e)}',
                ephemeral=True
            )


async def setup(bot: commands.Bot):
    """Setup function to add this cog to the bot."""
    await bot.add_cog(StandingsCog(bot))
