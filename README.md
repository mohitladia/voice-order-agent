# Voice Order Agent 🤖📞

AI-powered voice agent that automatically calls customers, takes orders via natural conversation, and sends WhatsApp confirmations.

## Features

- 📞 **Automated Phone Calls** - Initiates calls using Bland AI/Vapi
- 🗣️ **Natural Conversations** - LLM-powered order taking with context awareness
- 📱 **WhatsApp Confirmations** - Automatic order confirmation messages
- 💾 **Order Management** - SQLite database for order tracking
- 🔄 **Webhook Integration** - Real-time call status and completion handling
- 🎯 **Multi-tenant** - Support for multiple restaurants/businesses

## Architecture

```
Customer Trigger (WhatsApp/API)
    ↓
FastAPI Server initiates call
    ↓
Bland AI Voice Agent
    ↓
STT → LangChain Agent (order parsing) → TTS
    ↓
Save order to database
    ↓
Send WhatsApp confirmation (Twilio)
```

## Tech Stack

- **Backend**: FastAPI + Python 3.12
- **Voice AI**: Bland AI / Vapi.ai
- **LLM**: LangChain with OpenAI GPT-4
- **WhatsApp**: Twilio WhatsApp API
- **Database**: SQLite (dev) / PostgreSQL (prod)
- **Deployment**: Docker + Railway/Fly.io

## Setup

### Prerequisites

- Python 3.12+
- API Keys:
  - OpenAI API key
  - Bland AI / Vapi API key
  - Twilio Account SID + Auth Token
  - Twilio WhatsApp enabled number

### Installation

```bash
# Clone repository
git clone https://github.com/yourusername/voice-order-agent.git
cd voice-order-agent

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment template
cp .env.example .env
# Edit .env with your API keys
```

### Environment Variables

```env
OPENAI_API_KEY=sk-...
BLAND_AI_API_KEY=...
TWILIO_ACCOUNT_SID=...
TWILIO_AUTH_TOKEN=...
TWILIO_WHATSAPP_FROM=whatsapp:+14155238886
DATABASE_URL=sqlite:///./orders.db
WEBHOOK_BASE_URL=https://your-domain.com
```

### Run Locally

```bash
# Development server
uvicorn app.main:app --reload --port 8000

# For webhook testing, expose with ngrok
ngrok http 8000
# Update WEBHOOK_BASE_URL in .env
```

## API Endpoints

### Initiate Order Call

```bash
POST /api/v1/calls/initiate
Content-Type: application/json

{
  "customer_phone": "+919876543210",
  "customer_name": "John Doe",
  "business_id": "restaurant_1",
  "context": {
    "menu_items": ["Pizza", "Burger", "Pasta"],
    "previous_orders": []
  }
}
```

### Webhook - Call Complete

```bash
POST /webhooks/bland/call-complete
# Receives call transcript, extracts order, saves to DB, sends WhatsApp
```

### Get Order Status

```bash
GET /api/v1/orders/{order_id}
```

## Project Structure

```
voice-order-agent/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI app
│   ├── config.py               # Configuration
│   ├── models/
│   │   ├── order.py            # Order data models
│   │   └── call.py             # Call session models
│   ├── routes/
│   │   ├── calls.py            # Call initiation endpoints
│   │   └── orders.py           # Order CRUD endpoints
│   ├── services/
│   │   ├── bland_client.py     # Bland AI integration
│   │   ├── whatsapp_client.py  # Twilio WhatsApp client
│   │   ├── order_parser.py     # LangChain order extraction
│   │   └── database.py         # Database operations
│   └── webhooks/
│       └── bland_webhook.py    # Bland AI webhook handlers
├── docs/
│   ├── API.md                  # API documentation
│   └── DEPLOYMENT.md           # Deployment guide
├── tests/
│   └── test_order_parser.py
├── .env.example
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
└── README.md
```

## Usage Flow

1. **Trigger Call**:
   ```bash
   curl -X POST http://localhost:8000/api/v1/calls/initiate \
     -H "Content-Type: application/json" \
     -d '{"customer_phone": "+919876543210", "customer_name": "Mohit"}'
   ```

2. **Agent Calls Customer**: Bland AI initiates call, conversation happens

3. **Order Extracted**: Webhook receives transcript, LangChain extracts structured order

4. **WhatsApp Sent**: Twilio sends confirmation with order details

5. **Database Updated**: Order saved with status tracking

## Cost Estimate (per order)

- Voice call (2-3 min): ₹5-15
- WhatsApp message: ₹0.40
- LLM API calls: ₹1-2
- **Total: ~₹10-20/order**

## Deployment

### Docker

```bash
docker build -t voice-order-agent .
docker run -p 8000:8000 --env-file .env voice-order-agent
```

### Railway

```bash
# Install Railway CLI
npm i -g @railway/cli

# Login and deploy
railway login
railway init
railway up
```

## Roadmap

- [ ] Multi-language support (Hindi, English)
- [ ] Payment integration (Razorpay/Stripe)
- [ ] Voice biometrics for customer verification
- [ ] Analytics dashboard
- [ ] Retry logic for failed calls
- [ ] SMS fallback if WhatsApp unavailable

## License

MIT

## Author

Built with ❤️ by Mohit Ladia
