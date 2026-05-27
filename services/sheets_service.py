"""
Google Sheets Service

Handles all interactions with the Google Sheets document for the MTG Budget League.
"""

import os
from typing import Optional
from dataclasses import dataclass
from datetime import datetime

import gspread
from google.oauth2.service_account import Credentials
from dotenv import load_dotenv

load_dotenv()

# Google Sheets configuration
SHEET_ID = os.getenv('GOOGLE_SHEET_ID')
CREDENTIALS_PATH = os.getenv('GOOGLE_CREDENTIALS_PATH', 'credentials.json')

# Define the scope for Google Sheets API
SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
]

# Sheet names
PLAYERS_SHEET = 'Players'
BRACKETS = ['$60s', '$70s', '$80s', '$90s', '$100s']


@dataclass
class Player:
    """Represents a player in the league."""
    name: str
    commander: str
    deck_name: str
    deck_link: str
    commander_image: Optional[str] = None


@dataclass
class Game:
    """Represents a game record."""
    date: str
    location: str
    players: list[str]
    winner: str
    bracket: str
    win_condition: str = ''


@dataclass
class PlayerStanding:
    """Represents a player's standing in a bracket."""
    name: str
    wins: int
    losses: int


class GoogleSheetsService:
    """Service class for interacting with Google Sheets."""
    
    def __init__(self):
        """Initialize the Google Sheets service."""
        self.client = None
        self.spreadsheet = None
        self._connect()
    
    def _connect(self):
        """Establish connection to Google Sheets."""
        try:
            credentials = Credentials.from_service_account_file(
                CREDENTIALS_PATH,
                scopes=SCOPES
            )
            self.client = gspread.authorize(credentials)
            self.spreadsheet = self.client.open_by_key(SHEET_ID)
            print('Successfully connected to Google Sheets')
        except Exception as e:
            print(f'Failed to connect to Google Sheets: {e}')
            raise
    
    def _get_or_create_sheet(self, sheet_name: str) -> gspread.Worksheet:
        """Get a worksheet by name, or create it if it doesn't exist."""
        try:
            return self.spreadsheet.worksheet(sheet_name)
        except gspread.WorksheetNotFound:
            # Create the sheet with appropriate headers
            worksheet = self.spreadsheet.add_worksheet(title=sheet_name, rows=1000, cols=10)
            
            if sheet_name == PLAYERS_SHEET:
                worksheet.update('A1:E1', [['Name', 'Commander', 'Deck Name', 'Deck Link', 'Commander Image']])
            elif sheet_name in BRACKETS:
                worksheet.update('A1:D1', [['Date', 'Location', 'Players', 'Winner', 'Win Condition']])
            
            return worksheet
    
    # ==================== Player Operations ====================
    
    def get_all_players(self) -> list[Player]:
        """Get all players from the Players sheet."""
        sheet = self._get_or_create_sheet(PLAYERS_SHEET)
        records = sheet.get_all_records()
        
        players = []
        for record in records:
            players.append(Player(
                name=record.get('Name', ''),
                commander=record.get('Commander', ''),
                deck_name=record.get('Deck Name', ''),
                deck_link=record.get('Deck Link', ''),
                commander_image=record.get('Commander Image', '')
            ))
        
        return players
    
    def get_player_names(self) -> list[str]:
        """Get a list of all player names."""
        players = self.get_all_players()
        return [p.name for p in players if p.name]
    
    def get_player(self, name: str) -> Optional[Player]:
        """Get a specific player by name."""
        players = self.get_all_players()
        for player in players:
            if player.name.lower() == name.lower():
                return player
        return None
    
    def register_player(self, player: Player) -> bool:
        """Register a new player in the league."""
        try:
            sheet = self._get_or_create_sheet(PLAYERS_SHEET)
            
            # Add the new player row
            sheet.append_row([
                player.name,
                player.commander,
                player.deck_name,
                player.deck_link,
                player.commander_image or ''
            ])
            
            return True
        except Exception as e:
            print(f'Failed to register player: {e}')
            return False
    
    # ==================== Game Operations ====================
    
    def get_games_for_bracket(self, bracket: str) -> list[Game]:
        """Get all games for a specific bracket."""
        if bracket not in BRACKETS:
            raise ValueError(f'Invalid bracket: {bracket}. Must be one of {BRACKETS}')
        
        sheet = self._get_or_create_sheet(bracket)
        records = sheet.get_all_records()
        
        games = []
        for record in records:
            # Support both old format (Player 1-4 columns) and new format (Players column)
            if 'Players' in record:
                # New format: comma-separated players
                players_str = record.get('Players', '')
                players = [p.strip() for p in players_str.split(',') if p.strip()]
            else:
                # Old format: individual player columns (up to 6)
                players = [
                    record.get('Player 1', ''),
                    record.get('Player 2', ''),
                    record.get('Player 3', ''),
                    record.get('Player 4', ''),
                    record.get('Player 5', ''),
                    record.get('Player 6', '')
                ]
                players = [p for p in players if p]  # Filter empty
            
            games.append(Game(
                date=str(record.get('Date', '')),
                location=record.get('Location', ''),
                players=players,
                winner=record.get('Winner', ''),
                bracket=bracket,
                win_condition=record.get('Win Condition', '')
            ))
        
        return games
    
    def get_recent_game(self, bracket: Optional[str] = None) -> Optional[Game]:
        """Get the most recent game, optionally filtered by bracket."""
        recent_game = None
        recent_date = None
        
        brackets_to_check = [bracket] if bracket else BRACKETS
        
        for b in brackets_to_check:
            try:
                games = self.get_games_for_bracket(b)
                for game in games:
                    if game.date:
                        try:
                            game_date = datetime.strptime(game.date, '%m/%d/%Y')
                            if recent_date is None or game_date > recent_date:
                                recent_date = game_date
                                recent_game = game
                        except ValueError:
                            # Skip games with invalid date format
                            continue
            except Exception:
                continue
        
        return recent_game
    
    def record_game(self, game: Game) -> bool:
        """Record a new game in the appropriate bracket sheet."""
        try:
            if game.bracket not in BRACKETS:
                raise ValueError(f'Invalid bracket: {game.bracket}')
            
            if len(game.players) < 2 or len(game.players) > 6:
                raise ValueError(f'Game must have 2-6 players, got {len(game.players)}')
            
            sheet = self._get_or_create_sheet(game.bracket)
            
            # Check current headers to determine format
            headers = sheet.row_values(1)
            
            if 'Players' in headers:
                # New format: Players as comma-separated, with Win Condition
                players_str = ', '.join(game.players)
                sheet.append_row([
                    game.date,
                    game.location,
                    players_str,
                    game.winner,
                    game.win_condition
                ])
            else:
                # Old format: Pad players to 6, add Win Condition at the end
                players = game.players + [''] * (6 - len(game.players))
                row_data = [
                    game.date,
                    game.location,
                    players[0] if len(players) > 0 else '',
                    players[1] if len(players) > 1 else '',
                    players[2] if len(players) > 2 else '',
                    players[3] if len(players) > 3 else '',
                    players[4] if len(players) > 4 else '',
                    players[5] if len(players) > 5 else '',
                    game.winner,
                    game.win_condition  # Add to end - will create new column
                ]
                sheet.append_row(row_data)
                
                # Add Win Condition header if not present
                if 'Win Condition' not in headers:
                    sheet.update_cell(1, len(headers) + 1, 'Win Condition')
            
            return True
        except Exception as e:
            print(f'Failed to record game: {e}')
            return False
    
    # ==================== Standings Operations ====================
    
    def get_standings_for_bracket(self, bracket: str) -> list[PlayerStanding]:
        """Calculate standings for a specific bracket."""
        games = self.get_games_for_bracket(bracket)
        
        # Track wins and losses for each player
        player_stats: dict[str, dict[str, int]] = {}
        
        for game in games:
            for player in game.players:
                if player not in player_stats:
                    player_stats[player] = {'wins': 0, 'losses': 0}
                
                if player == game.winner:
                    player_stats[player]['wins'] += 1
                else:
                    player_stats[player]['losses'] += 1
        
        # Convert to PlayerStanding objects and sort by wins
        standings = [
            PlayerStanding(name=name, wins=stats['wins'], losses=stats['losses'])
            for name, stats in player_stats.items()
        ]
        
        standings.sort(key=lambda x: (-x.wins, x.losses))  # Sort by wins desc, then losses asc
        
        return standings
    
    def get_overall_standings(self) -> list[PlayerStanding]:
        """Calculate overall league standings by aggregating wins/losses across all brackets."""
        player_stats: dict[str, dict[str, int]] = {}

        for bracket in BRACKETS:
            try:
                games = self.get_games_for_bracket(bracket)
            except Exception:
                continue

            for game in games:
                for player in game.players:
                    if player not in player_stats:
                        player_stats[player] = {'wins': 0, 'losses': 0}

                    if player == game.winner:
                        player_stats[player]['wins'] += 1
                    else:
                        player_stats[player]['losses'] += 1

        standings = [
            PlayerStanding(name=name, wins=stats['wins'], losses=stats['losses'])
            for name, stats in player_stats.items()
        ]

        # Overall ranking is based on total wins only.
        standings.sort(key=lambda x: -x.wins)

        return standings

    def get_player_standings_all_brackets(self, player_name: str) -> dict[str, PlayerStanding]:
        """Get a player's standings across all brackets."""
        standings = {}
        
        for bracket in BRACKETS:
            bracket_standings = self.get_standings_for_bracket(bracket)
            for standing in bracket_standings:
                if standing.name.lower() == player_name.lower():
                    standings[bracket] = standing
                    break
        
        return standings
    
    def get_available_brackets(self) -> list[str]:
        """Get list of available brackets."""
        return BRACKETS.copy()


# Singleton instance
_service_instance: Optional[GoogleSheetsService] = None


def get_sheets_service() -> GoogleSheetsService:
    """Get the singleton instance of the Google Sheets service."""
    global _service_instance
    if _service_instance is None:
        _service_instance = GoogleSheetsService()
    return _service_instance
