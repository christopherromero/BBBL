# Battle Buddies Budget League Discord Bot

A Discord bot for managing MTG Budget League information stored in Google Sheets.

## Features

- **`/standings`** - View current standings for a single bracket or all brackets
- **`/league`** - View overall league standings, or a single player's overall record
- **`/player`** - Get detailed information about a specific player
- **`/players`** - List all registered players
- **`/register`** - Register a new player in the league
- **`/record`** - Record a new game with an interactive flow
- **`/recent`** - Get information about the most recent game

## Setup Instructions

### 1. Prerequisites

- Python 3.10 or higher
- A Discord account with a server where you have admin permissions
- A Google account

### 2. Create a Discord Bot

1. Go to the [Discord Developer Portal](https://discord.com/developers/applications)
2. Click "New Application" and give it a name (e.g., "Jace, League Archivist")
3. Go to the "Bot" section and click "Add Bot"
4. Under "Privileged Gateway Intents", enable:
   - Message Content Intent
5. Copy the bot token (you'll need this later)
6. Go to "OAuth2" > "URL Generator"
7. Select scopes: `bot`, `applications.commands`
8. Select bot permissions: `Send Messages`, `Embed Links`, `Use Slash Commands`
9. Copy the generated URL and open it to invite the bot to your server

### 3. Set Up Google Sheets API

1. Go to the [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project (or select an existing one)
3. Enable the **Google Sheets API** and **Google Drive API**:
   - Go to "APIs & Services" > "Library"
   - Search for and enable both APIs
4. Create a Service Account:
   - Go to "APIs & Services" > "Credentials"
   - Click "Create Credentials" > "Service Account"
   - Fill in the details and create
   - Click on the service account, go to "Keys" tab
   - Click "Add Key" > "Create new key" > JSON
   - Download the JSON file and save it as `credentials.json` in the project folder
5. Share your Google Sheet with the service account:
   - Open your Google Sheet
   - Click "Share"
   - Add the service account email (found in the JSON file as `client_email`)
   - Give it "Editor" access

### 4. Configure the Bot

1. Copy `.env.example` to `.env`:
   ```powershell
   Copy-Item .env.example .env
   ```

2. Edit `.env` with your values:
   ```
   DISCORD_BOT_TOKEN=your_discord_bot_token_here
   GOOGLE_SHEET_ID=1LGSRCPuxPVZD5CByZD_eV7m9aZmuYGWBwhQv6hQhRaM
   GOOGLE_CREDENTIALS_PATH=credentials.json
   ```

### 5. Set Up Your Google Sheet

The bot expects the following sheet structure:

#### Players Sheet (named "Players")
| Name | Commander | Deck Name | Deck Link | Commander Image |
|------|-----------|-----------|-----------|-----------------|
| Chris | Baba Lysaga | Into The Pot, Dearie | https://mtggoldfish.com/... | (optional URL) |

#### Bracket Sheets (named "$60s", "$70s", "$80s", "$90s", "$100s")
| Date | Location | Player 1 | Player 2 | Player 3 | Player 4 | Winner |
|------|----------|----------|----------|----------|----------|--------|
| 04/05/2026 | Chris' House | Chris | Morgan | Peter | Devon | Chris |

**Note:** The bot will automatically create these sheets with the correct headers if they don't exist!

### 6. Install Dependencies

```powershell
# Create a virtual environment (recommended)
python -m venv venv
.\venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt
```

### 7. Run the Bot

```powershell
python bot.py
```

You should see:
```
Successfully connected to Google Sheets
Jace, League Archivist#0744 has connected to Discord!
Synced 6 command(s)
```

## Usage Examples

### Get Standings
```
/standings bracket:$60 Bracket
```
Shows the current standings for the $60 bracket.

Other options:
- `/standings bracket:All Brackets` - Shows the top players in each bracket side-by-side.

### Get Overall League
```
/league
```
Shows the combined league standings across every bracket, ranked by total wins, with the current leader called out.

```
/league player:Chris
```
Shows a single player's overall record (total wins, games played, win %, and overall rank).

### Get Player Info
```
/player name:Chris
```
Shows Chris's deck info, commander, and standings across all brackets.

### Record a Game
```
/record
```
Starts an interactive flow to record a new game:
1. Select the bracket
2. Enter the date and location
3. Select the players
4. Select the winner

### Get Recent Game
```
/recent
```
Shows information about the most recently played game.

## Deploying to Synology NAS (Docker)

The bot is lightweight and perfect for running 24/7 on a Synology NAS using Container Manager (Docker).

### Prerequisites

- Synology NAS with DSM 7.0 or higher
- **Container Manager** package installed (from Package Center)
- SSH access enabled (optional, for command-line deployment)

### Method 1: Using Container Manager UI (Recommended)

#### Step 1: Prepare the Files

1. On your NAS, create a folder for the bot using File Station:
   - Navigate to a shared folder (e.g., `docker`)
   - Create a new folder called `bbbl-bot`
   - Full path example: `/volume1/docker/bbbl-bot`

2. Upload these files to the `bbbl-bot` folder:
   ```
   bbbl-bot/
   ├── bot.py
   ├── requirements.txt
   ├── Dockerfile
   ├── docker-compose.yml
   ├── .env
   ├── credentials.json
   ├── cogs/
   │   ├── __init__.py
   │   ├── standings.py
   │   ├── players.py
   │   └── games.py
   └── services/
       ├── __init__.py
       └── sheets_service.py
   ```

   You can upload via:
   - **File Station**: Drag and drop files
   - **SMB**: Map the NAS as a network drive and copy files
   - **SCP/SFTP**: Use a tool like WinSCP or the command line

#### Step 2: Create the Project in Container Manager

1. Open **Container Manager** from DSM
2. Go to **Project** in the left sidebar
3. Click **Create**
4. Configure the project:
   - **Project name**: `bbbl-bot`
   - **Path**: Select your `/docker/bbbl-bot` folder
   - **Source**: Select "Use existing docker-compose.yml"
5. Click **Next**
6. Review the settings and click **Done**

The container will build and start automatically.

#### Step 3: Verify It's Running

1. Go to **Container** in Container Manager
2. You should see `jace-league-archivist` with status "Running"
3. Click on the container → **Logs** tab
4. You should see:
   ```
   Successfully connected to Google Sheets
   Jace, League Archivist#0744 has connected to Discord!
   Synced 6 command(s)
   ```

### Method 2: Using SSH (Advanced)

1. SSH into your NAS:
   ```bash
   ssh admin@your-nas-ip
   ```

2. Navigate to your bot folder:
   ```bash
   cd /volume1/docker/bbbl-bot
   ```

3. Build and start the container:
   ```bash
   sudo docker-compose up -d --build
   ```

4. Check the logs:
   ```bash
   sudo docker-compose logs -f
   ```

5. Press `Ctrl+C` to exit logs (container keeps running)

### Managing the Bot

#### Restart the Bot
- **UI**: Container Manager → Container → Select container → Action → Restart
- **SSH**: `sudo docker-compose restart`

#### Stop the Bot
- **UI**: Container Manager → Container → Select container → Action → Stop
- **SSH**: `sudo docker-compose down`

#### Update the Bot

1. Upload the updated files to `/volume1/docker/bbbl-bot`, overwriting the old ones.
2. **UI (Container Manager)**:
   1. **Project** → select `bbbl-bot` → **Action** → **Stop**.
   2. **Action** → **Build** to rebuild the image.
   3. **Action** → **Start** to recreate the container from the new image.
3. **SSH** equivalent:
   ```bash
   cd /volume1/docker/bbbl-bot
   sudo docker-compose up -d --build --force-recreate
   ```

#### View Logs
- **UI**: Container Manager → Container → Select container → Logs
- **SSH**: `sudo docker-compose logs -f`

### Auto-Start on Boot

The `docker-compose.yml` includes `restart: unless-stopped`, which means:
- The bot automatically starts when your NAS boots up
- If the bot crashes, it will automatically restart
- It only stops if you manually stop it

### Resource Usage

The bot is very lightweight:
- **RAM**: ~50-100 MB
- **CPU**: Minimal (spikes only when processing commands)
- **Storage**: ~200 MB (including Python and dependencies)

### Troubleshooting Synology Deployment

#### Container won't start
- Check logs in Container Manager for error messages
- Verify `.env` file has correct tokens
- Ensure `credentials.json` is valid JSON

#### "Permission denied" errors
- Make sure the files have correct permissions
- Try: `sudo chmod -R 755 /volume1/docker/bbbl-bot`

#### Can't connect to Google Sheets
- Verify the service account email has Editor access to your Google Sheet
- Check that `credentials.json` was uploaded correctly (not corrupted)

#### Container keeps restarting
- Check logs for the actual error
- Common issues: invalid Discord token, Google API errors

## Troubleshooting

### "Failed to connect to Google Sheets"
- Make sure `credentials.json` exists in the project folder
- Verify the service account has access to the Google Sheet
- Check that the `GOOGLE_SHEET_ID` in `.env` is correct

### "Synced 0 command(s)"
- Wait a few minutes - Discord can take time to register slash commands
- Try restarting the bot

### Commands not showing up
- Make sure the bot has the `applications.commands` scope when invited
- Try kicking and re-inviting the bot with the correct permissions

## Project Structure

```
BBBL/
├── bot.py                 # Main bot entry point
├── requirements.txt       # Python dependencies
├── Dockerfile             # Docker container definition
├── docker-compose.yml     # Docker Compose configuration
├── .env                   # Environment variables (create from .env.example)
├── .env.example           # Example environment file
├── credentials.json       # Google service account credentials
├── cogs/
│   ├── __init__.py
│   ├── standings.py       # Standings commands
│   ├── players.py         # Player commands
│   └── games.py           # Game recording commands
└── services/
    ├── __init__.py
    └── sheets_service.py  # Google Sheets integration
```

## License

MIT License - Feel free to modify and use for your own leagues!
