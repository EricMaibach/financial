# AI Chat Feature Setup Guide

## Overview

The dashboard now includes an AI-powered chat assistant that can help users understand the market divergence data. The chat uses OpenAI's GPT-4 API and automatically feeds current market data as context.

## Features

- **Real-time market context**: The AI has access to current divergence gap, credit spreads, gold prices, VIX, S&P 500, and Bitcoin data
- **Smart assistance**: Ask questions about metrics, scenarios, historical context, and market dynamics
- **Conversational UI**: Floating chat button with smooth animations
- **Auto-generated summaries**: Market data is summarized from CSV files on each request

## Setup Instructions

### 1. Install Dependencies

Make sure you have the OpenAI Python package installed:

```bash
pip install -r requirements.txt
```

### 2. Set OpenAI API Key

You need to set the `OPENAI_API_KEY` environment variable. You have several options:

#### Option A: Set in terminal (temporary - lasts for session)

```bash
export OPENAI_API_KEY='your-api-key-here'
python dashboard.py
```

#### Option B: Create a .env file (recommended)

1. Create a file named `.env` in the signaltrackers directory:

```bash
OPENAI_API_KEY=your-api-key-here
```

2. Install python-dotenv:

```bash
pip install python-dotenv
```

3. Add to dashboard.py (at the top):

```python
from dotenv import load_dotenv
load_dotenv()
```

#### Option C: Set system-wide environment variable

**Linux/Mac:**
Add to `~/.bashrc` or `~/.zshrc`:
```bash
export OPENAI_API_KEY='your-api-key-here'
```

**Windows:**
```cmd
setx OPENAI_API_KEY "your-api-key-here"
```

### 3. Get an OpenAI API Key

1. Go to [https://platform.openai.com/api-keys](https://platform.openai.com/api-keys)
2. Sign in or create an account
3. Click "Create new secret key"
4. Copy the key (starts with `sk-...`)
5. Use this key in your environment variable

### 4. Start the Dashboard

```bash
python dashboard.py
```

The dashboard will run on [http://localhost:5000](http://localhost:5000)

## Using the Chat

1. Look for the purple robot button in the bottom-right corner
2. Click to open the chat window
3. Type your questions about the market data
4. Press Enter or click Send

## Example Questions

Try asking:
- "What does the divergence gap mean?"
- "Explain the credit spread situation"
- "What are the main risks right now?"
- "What scenarios could resolve this divergence?"
- "Why is gold so high?"
- "What's happening with Bitcoin?"

## Technical Details

### API Endpoint

The chat functionality uses a `/api/chat` endpoint that:
- Accepts POST requests with JSON: `{"message": "user question"}`
- Generates a market summary from current CSV data
- Sends to OpenAI GPT-4 with system context
- Returns JSON: `{"message": "AI response", "timestamp": "..."}`

### System Context

The AI receives:
- Current values for all key metrics
- Percentile rankings (how extreme current values are)
- 1-day changes and percentages
- Historical ranges (min/max)
- Instructions on how to interpret the data

### Cost Considerations

- Each chat message costs ~$0.01-0.03 (GPT-4 pricing)
- Market summary is ~500-800 tokens per request
- Responses limited to 800 tokens
- Consider using GPT-3.5-turbo for lower costs (change model in dashboard.py)

## Troubleshooting

### "OpenAI API key not configured" error

- Make sure `OPENAI_API_KEY` is set in your environment
- Restart the terminal/dashboard after setting the key
- Check the key is correct and active

### Chat button doesn't appear

- Make sure browser cache is cleared
- Check browser console for JavaScript errors
- Verify dashboard.js and dashboard.css are loading

### API rate limits

- OpenAI has rate limits based on your plan
- Free tier: 3 requests/minute
- Paid tier: Higher limits
- Add error handling for rate limit errors if needed

## Customization

### Change AI Model

In `dashboard.py`, change the model parameter:

```python
model="gpt-3.5-turbo"  # Cheaper, faster
# or
model="gpt-4"  # More accurate, more expensive
```

### Adjust Response Length

Change `max_tokens` parameter:

```python
max_tokens=1200  # Longer responses
# or
max_tokens=500   # Shorter responses
```

### Modify System Instructions

Edit the `system_message` variable in the `/api/chat` endpoint to change how the AI behaves.

## Security Notes

- **Never commit your API key to git**
- Add `.env` to `.gitignore` if using .env file
- Use environment variables, not hardcoded keys
- Consider adding rate limiting if exposing publicly
- Monitor OpenAI usage dashboard for unexpected costs

## Support

For issues:
1. Check OpenAI status: [https://status.openai.com/](https://status.openai.com/)
2. Verify API key is valid
3. Check browser console for errors
4. Review Flask logs for backend errors
