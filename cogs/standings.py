"""
Standings Cog

Handles commands related to league standings.
"""

from typing import Optional

import discord
from discord import app_commands
from discord.ext import commands

from services.sheets_service import get_sheets_service


class StandingsCog(commands.Cog):
    """Cog for handling standings-related commands."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.sheets = get_sheets_service()

    async def player_autocomplete(
        self,
        interaction: discord.Interaction,
        current: str,
    ) -> list[app_commands.Choice[str]]:
        """Autocomplete for registered player names."""
        names = self.sheets.get_player_names()
        return [
            app_commands.Choice(name=n, value=n)
            for n in names
            if current.lower() in n.lower()
        ][:25]

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
                embed = discord.Embed(
                    title='League Standings - All Brackets',
                    color=discord.Color.gold()
                )

                for b in self.sheets.get_available_brackets():
                    standings = self.sheets.get_standings_for_bracket(b)

                    if standings:
                        standings_text = '\n'.join([
                            f'{i+1}. **{s.name}** - {s.wins}W / {s.losses}L'
                            for i, s in enumerate(standings[:5])
                        ])
                    else:
                        standings_text = 'No games recorded yet'

                    embed.add_field(
                        name=f'{b} Bracket',
                        value=standings_text,
                        inline=False
                    )
            else:
                standings = self.sheets.get_standings_for_bracket(bracket.value)

                embed = discord.Embed(
                    title=f'{bracket.name} Standings',
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
                f'An error occurred while fetching standings: {str(e)}',
                ephemeral=True
            )

    @app_commands.command(
        name='league',
        description="Overall league standings, or a single player's overall record"
    )
    @app_commands.describe(player='Optional: show the overall record for a specific player')
    @app_commands.autocomplete(player=player_autocomplete)
    async def league(
        self,
        interaction: discord.Interaction,
        player: Optional[str] = None,
    ):
        """Report overall league results, ranked by total wins across all brackets."""
        await interaction.response.defer()

        try:
            standings = self.sheets.get_overall_standings()

            if not standings or standings[0].wins == 0:
                await interaction.followup.send(
                    'No games recorded yet in any bracket.',
                    ephemeral=True,
                )
                return

            if player:
                match = next(
                    (s for s in standings if s.name.lower() == player.lower()),
                    None,
                )

                if match is None:
                    await interaction.followup.send(
                        f'No overall results found for "{player}".',
                        ephemeral=True,
                    )
                    return

                # Rank by wins only; players tied on wins share a rank.
                rank = 1 + sum(1 for s in standings if s.wins > match.wins)
                total_games = match.wins + match.losses
                win_pct = (match.wins / total_games * 100) if total_games else 0.0

                embed = discord.Embed(
                    title=f'Overall League: {match.name}',
                    color=discord.Color.gold(),
                )
                embed.add_field(name='Wins', value=str(match.wins), inline=True)
                embed.add_field(name='Games Played', value=str(total_games), inline=True)
                embed.add_field(name='Win %', value=f'{win_pct:.1f}%', inline=True)
                embed.add_field(
                    name='Overall Rank',
                    value=f'#{rank} of {len(standings)}',
                    inline=False,
                )

                await interaction.followup.send(embed=embed)
                return

            top_wins = standings[0].wins
            leaders = [s.name for s in standings if s.wins == top_wins]

            if len(leaders) == 1:
                leader_line = f'Current Leader: **{leaders[0]}** ({top_wins} wins)'
            else:
                leader_line = (
                    f'Current Leaders (tied at {top_wins} wins): '
                    + ', '.join(f'**{name}**' for name in leaders)
                )

            standings_text = '\n'.join([
                f'{i+1}. **{s.name}** - {s.wins} wins'
                for i, s in enumerate(standings)
            ])

            embed = discord.Embed(
                title='Overall League Standings',
                description=(
                    'Ranked by total wins across all brackets.\n\n'
                    f'{leader_line}\n\n'
                    f'{standings_text}'
                ),
                color=discord.Color.gold(),
            )

            await interaction.followup.send(embed=embed)

        except Exception as e:
            await interaction.followup.send(
                f'An error occurred while fetching the overall league: {str(e)}',
                ephemeral=True,
            )


async def setup(bot: commands.Bot):
    """Setup function to add this cog to the bot."""
    await bot.add_cog(StandingsCog(bot))
