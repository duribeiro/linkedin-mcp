# LinkedIn MCP Server

[![Version](https://img.shields.io/static/v1?label=version&message=1.3.1&color=blue)](https://github.com/duribeiro/linkedin-mcp/releases) <!-- x-release-please-version -->

MCP (Model Context Protocol) server for the LinkedIn API. Give your AI agents native access to your LinkedIn profile, feed, posts, articles, and insights — no browser automation needed.

## 📁 Project Structure

```
.
├── .github/
│   └── workflows/
│       └── ci.yml
├── tools/
│   ├── articles.py
│   ├── feed.py
│   ├── insights.py
│   ├── posts.py
│   └── profile.py
├── tests/
│   └── test_basic.py
├── auth.py
├── linkedin_config.json
├── server.py
├── pyproject.toml
├── requirements.txt
├── README.md
└── CHANGELOG.md
```

## ✨ Features

- 🔐 **OAuth 2.0 (3-legged)** — secure, standards-compliant auth with auto-refresh
- 📝 **Posts** — create text posts with optional link/image
- 🔗 **Share Link** — share a link with a customized preview card
- 👤 **Profile** — read your own profile data
- 📰 **Feed** — browse your LinkedIn feed
- 📊 **Insights** — get post/article share stats (impressions, likes, comments)

## 🛠️ Available Tools

| Tool | Description |
|------|-------------|
| `get_my_profile` | Fetch your LinkedIn profile |
| `get_my_feed` | Browse your LinkedIn feed |
| `create_post` | Create a text post (with optional link/image) |
| `share_link` | Share a link with a customized preview card |
| `get_my_articles` | List your published articles |
| `get_share_stats` | Get metrics for a post/article |

**Coming soon:** messaging, network management, job search.

## 🚀 Quick Start

### Prerequisites

- Python 3.11+

### 1. Create a LinkedIn App (2 minutes, free)

1. Go to [LinkedIn Developer Portal](https://www.linkedin.com/developers/apps)
2. Click **"Create App"**
3. Fill in:
   - **App name**: anything you like (e.g., "My AI Assistant")
   - **LinkedIn Page**: your personal page or company page
   - **App logo**: optional
4. Go to the **"Auth"** tab
5. Under **"Authorized redirect URLs"**, add:
   ```
   http://localhost:8080/callback
   ```
6. Copy your **Client ID** and **Client Secret**

### 2. Install

```bash
# Clone the repo
git clone https://github.com/duribeiro/linkedin-mcp.git
cd linkedin-mcp

# Install
pip install -e .
```

### 3. Configure

Create a `.env` file (copy from `.env.example`):

```bash
cp .env.example .env
```

Edit `.env` with your credentials:

```env
LINKEDIN_CLIENT_ID=your_client_id_here
LINKEDIN_CLIENT_SECRET=your_client_secret_here
LINKEDIN_REDIRECT_URI=http://localhost:8080/callback
```

### 4. Add to your AI agent

Add this to your agent's MCP config (e.g., `~/.hermes/config.yaml`, Claude Desktop config, or any MCP client):

```yaml
mcp_servers:
  linkedin:
    command: python
    args:
      - -m
      - server
    env:
      LINKEDIN_REDIRECT_URI: http://localhost:8080/callback
    env_keys:
      - LINKEDIN_CLIENT_ID
      - LINKEDIN_CLIENT_SECRET
```

For Hermes Agent specifically:

```bash
hermes mcp add linkedin -- python -m server \
  --env LINKEDIN_CLIENT_ID=your_id \
  --env LINKEDIN_CLIENT_SECRET=your_secret
```

### 5. Authenticate (first time only)

On the first tool call, the server opens your browser for OAuth:

1. Browser opens → log in to LinkedIn → authorize your app
2. You're redirected to `localhost:8080/callback` → token saved automatically
3. Done! The agent can now use all LinkedIn tools

The access token is saved to `~/.hermes/mcp-servers/linkedin/token.json`.

## 🔄 Token Lifecycle

- **Access token**: valid for 60 days
- **Refresh tokens**: available only for approved [Marketing Developer Platform (MDP)](https://learn.microsoft.com/en-us/linkedin/shared/authentication/programmatic-refresh-tokens) partners

For non-MDP apps (like this one), re-authorization is needed every 60 days. The auth flow takes 30 seconds.

> **Pro tip:** Set a calendar reminder or cron job to re-auth every 55 days. The server detects expired tokens and falls back to the OAuth flow automatically.

## 🔒 Security

- `.env` and `token.json` are in `.gitignore` — never committed
- Tokens are stored locally on your machine only
- Each developer must create their own LinkedIn app (free, instant)
- The 3-legged OAuth flow means your credentials never touch our servers

## 🧪 Testing

```bash
# Start the server in dev mode
python server.py
```

Then use any MCP client to call the tools.

## 📄 License

MIT — see [LICENSE](LICENSE) file.

## 👤 Author

Created by [Eduardo Ribeiro](https://github.com/duribeiro) with ❤️ and Hermes Agent.

---

⭐ **If this is useful, star the repo!** Questions? Open an issue.
