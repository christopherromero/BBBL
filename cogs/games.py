"""
Games Cog

Handles commands related to game recording and game information.
"""

import discord
from discord import app_commands
from discord.ext import commands
from typing import Optional, List

from services.sheets_service import get_sheets_service, Game


class GameRecordView(discord.ui.View):
    """View for recording a new game with step-by-step prompts."""
    
    def __init__(self, sheets_service, interaction: discord.Interaction):
        super().__init__(timeout=300)  # 5 minute timeout
        self.sheets = sheets_service
        self.original_interaction = interaction
        self.game_data = {
            'date': None,
            'location': None,
            'players': [],
            'winner': None,
            'bracket': None,
            'win_condition': None
        }
        self.current_step = 'bracket'
        self.message = None
    
    async def start(self):
        """Start the game recording process."""
        await self.show_bracket_select()
    
    async def show_bracket_select(self):
        """Show bracket selection."""
        self.clear_items()
        
        bracket_select = discord.ui.Select(
            placeholder='Select the bracket...',
            options=[
                discord.SelectOption(label='$60 Bracket', value='$60s'),
                discord.SelectOption(label='$70 Bracket', value='$70s'),
                discord.SelectOption(label='$80 Bracket', value='$80s'),
                discord.SelectOption(label='$90 Bracket', value='$90s'),
                discord.SelectOption(label='$100 Bracket', value='$100s'),
            ]
        )
        bracket_select.callback = self.bracket_selected
        self.add_item(bracket_select)
        
        embed = discord.Embed(
            title='Record a Game',
            description='**Step 1/6:** Which bracket was this game in?',
            color=discord.Color.green()
        )
        
        await self.original_interaction.followup.send(embed=embed, view=self)
    
    async def bracket_selected(self, interaction: discord.Interaction):
        """Handle bracket selection."""
        self.game_data['bracket'] = interaction.data['values'][0]
        await interaction.response.send_modal(GameDateLocationModal(self))
    
    async def show_player_select(self, interaction: discord.Interaction):
        """Show player multi-select."""
        self.clear_items()
        
        players = self.sheets.get_player_names()
        
        if len(players) < 2:
            await interaction.response.send_message(
                'Not enough players registered. Please register players first.',
                ephemeral=True
            )
            return
        
        player_select = discord.ui.Select(
            placeholder='Select all players in this game (2-6)...',
            min_values=2,
            max_values=min(6, len(players)),
            options=[
                discord.SelectOption(label=p, value=p)
                for p in players[:25]  # Discord limit
            ]
        )
        player_select.callback = self.players_selected
        self.add_item(player_select)
        
        embed = discord.Embed(
            title='Record a Game',
            description=f'**Step 3/6:** Who played in this game?\n\n'
                       f'Date: {self.game_data["date"]}\n'
                       f'Location: {self.game_data["location"]}\n'
                       f'Bracket: {self.game_data["bracket"]}',
            color=discord.Color.green()
        )
        
        await interaction.response.edit_message(embed=embed, view=self)
    
    async def players_selected(self, interaction: discord.Interaction):
        """Handle player selection."""
        self.game_data['players'] = interaction.data['values']
        await self.show_winner_select(interaction)
    
    async def show_winner_select(self, interaction: discord.Interaction):
        """Show winner selection."""
        self.clear_items()
        
        winner_select = discord.ui.Select(
            placeholder='Select the winner...',
            options=[
                discord.SelectOption(label=p, value=p)
                for p in self.game_data['players']
            ]
        )
        winner_select.callback = self.winner_selected
        self.add_item(winner_select)
        
        players_str = ', '.join(self.game_data['players'])
        
        embed = discord.Embed(
            title='Record a Game',
            description=f'**Step 4/6:** Who won the game?\n\n'
                       f'Date: {self.game_data["date"]}\n'
                       f'Location: {self.game_data["location"]}\n'
                       f'Bracket: {self.game_data["bracket"]}\n'
                       f'Players: {players_str}',
            color=discord.Color.green()
        )
        
        await interaction.response.edit_message(embed=embed, view=self)
    
    async def winner_selected(self, interaction: discord.Interaction):
        """Handle winner selection and show win condition modal."""
        self.game_data['winner'] = interaction.data['values'][0]
        await interaction.response.send_modal(WinConditionModal(self))
    
    async def save_game(self, interaction: discord.Interaction):
        """Save the game after all data is collected."""
        game = Game(
            date=self.game_data['date'],
            location=self.game_data['location'],
            players=self.game_data['players'],
            winner=self.game_data['winner'],
            bracket=self.game_data['bracket'],
            win_condition=self.game_data['win_condition']
        )
        
        success = self.sheets.record_game(game)
        
        self.clear_items()
        
        if success:
            players_str = ', '.join([p for p in self.game_data['players'] if p])
            
            embed = discord.Embed(
                title='Game Recorded!',
                description=f'The game has been successfully recorded.',
                color=discord.Color.green()
            )
            embed.add_field(name='Date', value=self.game_data['date'], inline=True)
            embed.add_field(name='Location', value=self.game_data['location'], inline=True)
            embed.add_field(name='Bracket', value=self.game_data['bracket'], inline=True)
            embed.add_field(name='Players', value=players_str, inline=False)
            embed.add_field(name='Winner', value=self.game_data['winner'], inline=True)
            embed.add_field(name='Win Condition', value=self.game_data['win_condition'], inline=True)
        else:
            embed = discord.Embed(
                title='Failed to Record Game',
                description='An error occurred while recording the game. Please try again.',
                color=discord.Color.red()
            )
        
        await interaction.response.edit_message(embed=embed, view=self)
        self.stop()


class GameDateLocationModal(discord.ui.Modal, title='Game Details'):
    """Modal for entering game date and location."""
    
    date = discord.ui.TextInput(
        label='Date (MM/DD/YYYY)',
        placeholder='04/05/2026',
        required=True,
        max_length=10
    )
    
    location = discord.ui.TextInput(
        label='Location',
        placeholder="At Chris' House",
        required=True,
        max_length=100
    )
    
    def __init__(self, view: GameRecordView):
        super().__init__()
        self.view = view
    
    async def on_submit(self, interaction: discord.Interaction):
        """Handle the modal submission."""
        self.view.game_data['date'] = str(self.date.value)
        self.view.game_data['location'] = str(self.location.value)
        await self.view.show_player_select(interaction)


class WinConditionModal(discord.ui.Modal, title='Win Condition'):
    """Modal for entering the win condition."""
    
    win_condition = discord.ui.TextInput(
        label='How did they win?',
        placeholder='Combat damage, combo, mill, etc.',
        required=True,
        max_length=200
    )
    
    def __init__(self, view: GameRecordView):
        super().__init__()
        self.view = view
    
    async def on_submit(self, interaction: discord.Interaction):
        """Handle the modal submission and save the game."""
        self.view.game_data['win_condition'] = str(self.win_condition.value)
        await self.view.save_game(interaction)


class GamesCog(commands.Cog):
    """Cog for handling game-related commands."""
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.sheets = get_sheets_service()
    
    @app_commands.command(name='record', description='Record a new game')
    async def record_game(self, interaction: discord.Interaction):
        """Start the game recording process."""
        await interaction.response.defer()
        
        view = GameRecordView(self.sheets, interaction)
        await view.start()
    
    @app_commands.command(name='recent', description='Get information about the most recent game')
    @app_commands.describe(bracket='Optionally filter by bracket')
    @app_commands.choices(bracket=[
        app_commands.Choice(name='$60 Bracket', value='$60s'),
        app_commands.Choice(name='$70 Bracket', value='$70s'),
        app_commands.Choice(name='$80 Bracket', value='$80s'),
        app_commands.Choice(name='$90 Bracket', value='$90s'),
        app_commands.Choice(name='$100 Bracket', value='$100s'),
    ])
    async def recent_game(
        self,
        interaction: discord.Interaction,
        bracket: Optional[app_commands.Choice[str]] = None
    ):
        """Get information about the most recent game."""
        await interaction.response.defer()
        
        try:
            bracket_value = bracket.value if bracket else None
            game = self.sheets.get_recent_game(bracket_value)
            
            if not game:
                await interaction.followup.send(
                    'No games recorded yet.' + (f' in the {bracket.name}' if bracket else ''),
                    ephemeral=True
                )
                return
            
            # Get winner's commander if available
            winner_info = self.sheets.get_player(game.winner)
            commander_text = f' with **{winner_info.commander}**' if winner_info else ''
            
            players = game.players
            players_str = ', '.join(players[:-1]) + f', and {players[-1]}' if len(players) > 1 else players[0] if players else 'None'
            
            embed = discord.Embed(
                title='Most Recent Game',
                color=discord.Color.purple()
            )
            
            embed.add_field(name='Date', value=game.date, inline=True)
            embed.add_field(name='Location', value=game.location, inline=True)
            embed.add_field(name='Bracket', value=game.bracket, inline=True)
            embed.add_field(name='Players', value=players_str, inline=False)
            embed.add_field(name='Winner', value=f'{game.winner}{commander_text}', inline=True)
            if game.win_condition:
                embed.add_field(name='Win Condition', value=game.win_condition, inline=True)
            
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            await interaction.followup.send(
                f'An error occurred: {str(e)}',
                ephemeral=True
            )


async def setup(bot: commands.Bot):
    """Setup function to add this cog to the bot."""
    await bot.add_cog(GamesCog(bot))
