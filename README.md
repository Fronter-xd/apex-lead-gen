# Apex Lead Generation Engine

**An autonomous AI-powered lead generation system for identifying and engaging potential customers on Reddit and Twitter.**

## Overview

Apex-Lead-Gen is a sophisticated lead generation engine that monitors social platforms (Reddit and Twitter) for specific keywords related to ADHD productivity, routine management, and task organization. Using local Llama-3 AI, it drafts personalized outreach messages to potential leads.

## Features

- **Multi-Platform Monitoring**: Tracks Reddit and Twitter for target keywords
- **Keyword Targeting**: Monitors 'ADHD tax', 'productivity help', 'routine manager'
- **AI-Powered Drafting**: Uses local Llama-3 (Ollama) for personalized outreach
- **Lead Scoring**: Ranks leads based on engagement and relevance
- **PostgreSQL Storage**: Persistent lead database with full history
- **Zero API Costs**: Runs entirely on local infrastructure

## System Architecture

```mermaid
sequenceDiagram
    participant User as User
    participant Apex as Apex-Lead-Gen
    participant Reddit as Reddit (PRAW)
    participant Twitter as Twitter (Tweepy)
    participant Ollama as Ollama (Llama-3)
    participant DB as PostgreSQL

    User->>Apex: Start monitoring
    Apex->>Reddit: Scrape posts with keywords
    Apex->>Twitter: Scrape tweets with keywords
    
    loop Continuous Monitoring
        Reddit-->>Apex: New posts found
        Twitter-->>Apex: New tweets found
        
        Apex->>Apex: Score lead relevance
        Apex->>Apex: Filter duplicates
        
        alt Lead meets threshold
            Apex->>Ollama: Send context + prompt
            Ollama-->>Apex: Personalized draft
            
            Apex->>DB: Store lead + draft
            Apex->>User: Notify new lead ready
        end
    end
    
    User->>Apex: Review lead
    Apex-->>User: Display lead + draft message
    User->>Apex: Approve/Reject
```

## Tech Stack

| Component | Technology |
|-----------|------------|
| Language | Python 3.11+ |
| Reddit API | PRAW |
| Twitter API | Tweepy |
| AI Model | Llama-3 (via Ollama) |
| Database | PostgreSQL |
| Containerization | Docker Compose |

## Prerequisites

- Python 3.11 or higher
- Docker and Docker Compose
- Ollama running locally with Llama-3 model
- Reddit API credentials (client_id, client_secret)
- Twitter/X Developer credentials (API keys)

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/rousanraahat/apex-lead-gen.git
cd apex-lead-gen
```

### 2. Set Up Environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Configure Credentials

Create `config/credentials.env`:

```env
# Reddit API (PRAW)
REDDIT_CLIENT_ID=your_client_id
REDDIT_CLIENT_SECRET=your_client_secret
REDDIT_USERNAME=your_username
REDDIT_PASSWORD=your_password
REDDIT_USER_AGENT=ApexLeadGen/1.0

# Twitter API (Tweepy)
TWITTER_API_KEY=your_api_key
TWITTER_API_SECRET=your_api_secret
TWITTER_ACCESS_TOKEN=your_access_token
TWITTER_ACCESS_SECRET=your_access_token_secret
TWITTER_BEARER_TOKEN=your_bearer_token

# Ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3

# Database
DATABASE_URL=postgresql://apex:apex_secret@localhost:5432/apex_leads
```

### 4. Start PostgreSQL

```bash
docker-compose up -d
```

### 5. Initialize Database

```bash
python -m src.db init
```

### 6. Start Ollama (Separate Terminal)

```bash
ollama serve
ollama pull llama3
```

### 7. Run Apex-Lead-Gen

```bash
python -m src.leads run
```

## Usage

### Command Line Interface

```bash
# Start continuous monitoring
python -m src.leads run

# Check for new leads once
python -m src.leads scrape

# View recent leads
python -m src.leads list

# View a specific lead
python -m src.leads view <lead_id>

# Export leads to CSV
python -m src.leads export --format csv
```

### Configuration Options

Edit `config/settings.yaml`:

```yaml
monitoring:
  keywords:
    - "ADHD tax"
    - "productivity help"
    - "routine manager"
  platforms:
    - reddit
    - twitter
  interval_minutes: 15

scoring:
  engagement_threshold: 5
  relevance_weight: 0.7
  recent_weight: 0.3

outreach:
  auto_draft: true
  draft_style: "professional but friendly"
  max_draft_length: 280
```

## Project Structure

```
apex-lead-gen/
├── config/
│   ├── credentials.env.example
│   └── settings.yaml
├── src/
│   ├── __init__.py
│   ├── leads.py              # Main entry point
│   ├── scrapers/
│   │   ├── __init__.py
│   │   ├── reddit_scraper.py
│   │   └── twitter_scraper.py
│   ├── services/
│   │   ├── __init__.py
│   │   ├── lead_scorer.py
│   │   └── message_drafter.py
│   └── db/
│       ├── __init__.py
│       ├── models.py
│       └── database.py
├── tests/
│   ├── __init__.py
│   ├── test_scrapers.py
│   └── test_services.py
├── docker-compose.yml
├── requirements.txt
├── README.md
└── .gitignore
```

## Lead Scoring Algorithm

Leads are scored based on multiple factors:

| Factor | Weight | Description |
|--------|--------|-------------|
| Engagement | 40% | Upvotes, retweets, comments |
| Recency | 30% | How recent the post is |
| Relevance | 30% | Keyword density match |

Leads scoring above the threshold are automatically drafted and stored.

## Message Drafting

The Llama-3 model is prompted with:

```
You are a helpful assistant drafting personalized outreach messages.

Context: {lead_context}
Platform: {platform}
Original Post: {post_content}

Task: Draft a {platform} response that:
1. Shows genuine understanding of their challenge
2. Offers helpful value (not spammy)
3. Naturally introduces how you might help
4. Stays under {max_length} characters

Tone: {tone}

Draft your response:
```

## Database Schema

```sql
CREATE TABLE leads (
    id SERIAL PRIMARY KEY,
    platform VARCHAR(20) NOT NULL,
    post_id VARCHAR(100) NOT NULL UNIQUE,
    author VARCHAR(100) NOT NULL,
    content TEXT NOT NULL,
    url TEXT NOT NULL,
    engagement_score INTEGER DEFAULT 0,
    relevance_score FLOAT DEFAULT 0,
    total_score FLOAT DEFAULT 0,
    status VARCHAR(20) DEFAULT 'new',
    drafted_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE scrape_logs (
    id SERIAL PRIMARY KEY,
    platform VARCHAR(20) NOT NULL,
    posts_found INTEGER DEFAULT 0,
    new_leads INTEGER DEFAULT 0,
    errors TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

MIT License - See [LICENSE](LICENSE) for details.

## Disclaimer

This tool is for legitimate outreach purposes only. Always comply with platform Terms of Service and respect user privacy. Do not use for spam or harassment.
