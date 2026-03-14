# 🦞 Eliza Lobster - AI-Powered Bounty Agent on Solana

A sophisticated AI agent built on **ElizaOS** that assigns crypto bounties and automates payouts on the **Solana blockchain**. Eliza Lobster operates as a crypto-native bounty master, distributing rewards through SPL tokens (SOL and USDC) while maintaining complete transparency and security.

CA : 3y9BBL8Msh4XmtFLLUDquPa1o7wqy5TXdbPKSc3rpump

---

## 📋 Table of Contents
- [How Eliza Lobster Works](#how-eliza-lobster-works)
- [Features](#features)
- [Architecture](#architecture)
- [Installation](#installation)
- [Environment Setup](#environment-setup)
- [API Endpoints](#api-endpoints)
- [Usage Examples](#usage-examples)
- [Bounty System](#bounty-system)
- [Security Considerations](#security-considerations)
- [Deployment](#deployment)

---

## 🦀 How Eliza Lobster Works

### System Overview
Eliza Lobster operates in cycles, much like a lobster molting through different stages:

```
Task Pool → User Request → Task Assignment → Completion → Verification → Payout
```

### The Lobster Lifecycle

#### **Stage 1: Task Pool Creation** 🏚️
- Tasks are stored in a centralized pool with complete metadata:
  - **Title & Description**: Clear task objectives
  - **Reward Amount**: SOL or USDC tokens
  - **Difficulty Level**: Easy, Medium, or Hard
  - **Category**: Social, Development, Content, etc.
  - **Time Limit**: Expected completion window

#### **Stage 2: Task Discovery** 🔍
Users interact with the `/api/tasks` endpoint to:
- Browse all active bounties
- Filter by category, difficulty, or reward amount
- Review task requirements and timelines
- Select tasks aligned with their skills

#### **Stage 3: Bounty Request** 📝
When a user requests a task:
```
POST /api/bounties/request
{
  "userId": "user123",
  "taskId": "task-uuid",
  "wallet": "SolanaWalletAddress"
}
```

The system:
- Validates the wallet address (on-curve verification)
- Creates a bounty record with "pending" status
- Timestamps the request for audit trails
- Allocates the task to the user

#### **Stage 4: Work Completion** ✅
User completes the assigned task (tweet, code deployment, content creation, etc.)

#### **Stage 5: Submission & Verification** 🔐
User submits proof of completion:
```
POST /api/bounties/complete
{
  "userId": "user123",
  "taskId": "task-uuid",
  "wallet": "SolanaWalletAddress",
  "proofUrl": "proof-link"
}
```

The system verifies:
- Valid wallet format and on-curve status
- Task existence and reward details
- Bounty status tracking

#### **Stage 6: Automated Payout** 💰
Based on the reward token type:

**For SOL Payouts:**
- Converts reward to lamports (1 SOL = 1 billion lamports)
- Creates a SystemProgram transfer instruction
- Signs and confirms transaction
- Returns transaction hash for verification

**For USDC Payouts:**
- Locates Associated Token Accounts (ATAs)
- Uses USDC mint address (mainnet standard)
- Creates SPL token transfer instruction
- Executes with 6 decimal precision
- Records transaction confirmation

#### **Stage 7: Record & Confirmation** 📊
- Transaction hash stored permanently
- Bounty status updated to "paid"
- Completion timestamp recorded
- On-chain proof available for audit

---

## ✨ Features

### Core Functionality
- ✅ **Task Management**: Create, list, and categorize crypto bounties
- ✅ **Multi-Token Support**: Both SOL and USDC payouts
- ✅ **Solana Integration**: Direct blockchain transactions via Web3.js
- ✅ **Wallet Validation**: On-curve Solana address verification
- ✅ **Error Handling**: Comprehensive error messages and logging
- ✅ **Audit Trail**: Complete transaction history with timestamps

### Security Features
- ✅ **Private Key Management**: Secure keypair handling with BS58 encoding
- ✅ **Input Validation**: All wallet addresses verified before payout
- ✅ **Amount Verification**: Prevents zero or negative transfers
- ✅ **Confirmation Requirement**: All transactions confirmed before acceptance
- ✅ **Logging**: Detailed logs for audit and debugging

### Developer Features
- ✅ **RESTful API**: Clean, documented endpoints
- ✅ **TypeScript**: Full type safety and IDE support
- ✅ **Express Server**: Modern Node.js framework
- ✅ **Environment Variables**: Secure configuration management
- ✅ **Structured Responses**: Consistent JSON API responses

---

## 🏗️ Architecture

### Technology Stack
```
┌─────────────────────────────────────────────┐
│         Eliza Lobster System                │
├─────────────────────────────────────────────┤
│ Frontend/Client                             │
│  (REST API Consumer)                        │
└────────────────┬────────────────────────────┘
                 │
         ┌───────▼────────┐
         │  Express Server │
         │   (Port 3000)   │
         └───────┬────────┘
                 │
    ┌────────────┼────────────┐
    │            │            │
┌───▼────┐  ┌───▼────┐  ┌───▼──────┐
│ Routes │  │ Tasks  │  │ Solana   │
│ /api/* │  │ System │  │ Payout   │
└────────┘  └────────┘  └───┬──────┘
                             │
                    ┌────────▼────────┐
                    │  Solana Network  │
                    │  (RPC Connection)│
                    │  (Web3.js)       │
                    └──────────────────┘
```

### Data Flow

**Bounty Submission Process:**
```typescript
User Request
    ↓
Input Validation
    ↓
Bounty Creation
    ↓
Storage (In-Memory Map)
    ↓
Response with Status
```

**Payout Process:**
```typescript
Bounty Completion
    ↓
Wallet Validation
    ↓
Token Selection (SOL/USDC)
    ↓
Transaction Construction
    ↓
Keypair Signing
    ↓
Send to Network
    ↓
Confirmation Wait
    ↓
Update Records
```

---

## 📦 Installation

### Prerequisites
- **Node.js** 16+ and npm
- **Solana Wallet** with funded treasury account
- **Environment Variables** configured
- **RPC Endpoint** (e.g., Helius, QuickNode, or public Solana RPC)

### Step 1: Clone and Install
```bash
git clone https://github.com/yourusername/eliza-lobster.git
cd eliza-lobster

npm install
```

### Step 2: Build TypeScript
```bash
npm run build
```

### Step 3: Configure Environment
```bash
cp .env.example .env
# Edit .env with your values
```

### Step 4: Run Development Server
```bash
npm run dev
```

---

## 🔑 Environment Setup

Create a `.env` file in the project root:

```env
# Solana RPC Endpoint
SOLANA_RPC=https://api.mainnet-beta.solana.com
# Or use a custom RPC provider:
# SOLANA_RPC=https://your-rpc-endpoint.com

# Treasury Private Key (BS58 Encoded)
# Generate: solana-keygen new --outfile treasury.json
# Extract: cat treasury.json | jq -r '.[0:32]' | base58 encode
TREASURY_PRIVATE_KEY=YourBase58EncodedPrivateKey

# Server Configuration
PORT=3000
NODE_ENV=development
```

### How to Get Your Private Key

**Using Solana CLI:**
```bash
# Generate a new wallet
solana-keygen new --outfile treasury.json

# Extract and encode the secret key
solana-keygen show treasury.json --outfile -
```

**Using JavaScript:**
```javascript
import bs58 from 'bs58';
import fs from 'fs';

const keyfile = JSON.parse(fs.readFileSync('treasury.json'));
const secretKey = keyfile.slice(0, 32);
const bs58Encoded = bs58.encode(Buffer.from(secretKey));
console.log(bs58Encoded);
```

⚠️ **SECURITY WARNING**: Never commit `.env` file to version control!

---

## 🚀 API Endpoints

### Task Management

#### Get All Tasks
```http
GET /api/tasks
```

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "id": "uuid",
      "title": "Tweet about Eliza Lobster",
      "description": "Create engaging tweet...",
      "reward": 10,
      "rewardToken": "USDC",
      "category": "social",
      "difficulty": "easy",
      "timeLimit": 60,
      "createdAt": "2024-03-02T10:00:00Z",
      "isActive": true
    }
  ],
  "timestamp": "2024-03-02T10:30:45Z"
}
```

#### Get Single Task
```http
GET /api/tasks/:taskId
```

#### Get Tasks by Category
```http
GET /api/tasks/category/social
GET /api/tasks/category/development
GET /api/tasks/category/content
```

### Bounty Management

#### Request a Bounty
```http
POST /api/bounties/request
Content-Type: application/json

{
  "userId": "user123",
  "taskId": "task-uuid-here",
  "wallet": "9B5X76QSPSLvz4YEKMHzKjK8n3RQcZhdKCdR4YYScah8"
}
```

**Response (Success - 201):**
```json
{
  "success": true,
  "data": {
    "taskId": "task-uuid",
    "userId": "user123",
    "wallet": "9B5X76QSPSLvz4YEKMHzKjK8n3RQcZhdKCdR4YYScah8",
    "status": "pending",
    "reward": 10,
    "rewardToken": "USDC",
    "submittedAt": "2024-03-02T10:35:00Z"
  },
  "timestamp": "2024-03-02T10:35:00Z"
}
```

#### Complete Bounty & Receive Payout
```http
POST /api/bounties/complete
Content-Type: application/json

{
  "userId": "user123",
  "taskId": "task-uuid-here",
  "wallet": "9B5X76QSPSLvz4YEKMHzKjK8n3RQcZhdKCdR4YYScah8",
  "proofUrl": "https://twitter.com/user/status/1234567890"
}
```

**Response (Success - 200):**
```json
{
  "success": true,
  "data": {
    "txHash": "5KXhT6YJ8FqK2pL9nM3oQ1rS4tU5vW6xY7zA8bC9dE0FgH1iJ2kL3mN4oP5qR6sT7uV8wX9yZ0aB1cD2eE3fG4h",
    "bountyId": "user123-task-uuid"
  },
  "timestamp": "2024-03-02T10:40:00Z"
}
```

#### Get User's Bounties
```http
GET /api/bounties/user123
```

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "taskId": "task-uuid",
      "userId": "user123",
      "wallet": "9B5X76QSPSLvz4YEKMHzKjK8n3RQcZhdKCdR4YYScah8",
      "status": "paid",
      "reward": 10,
      "rewardToken": "USDC",
      "transactionHash": "5KXhT6YJ8FqK2pL9nM3oQ1rS4tU5vW6xY7zA8bC9dE0FgH1iJ2kL3mN4oP5qR6sT7uV8wX9yZ0aB1cD2eE3fG4h",
      "submittedAt": "2024-03-02T10:35:00Z",
      "completedAt": "2024-03-02T10:40:00Z"
    }
  ],
  "timestamp": "2024-03-02T10:45:00Z"
}
```

#### Health Check
```http
GET /health
```

**Response:**
```json
{
  "status": "healthy",
  "service": "eliza-lobster",
  "timestamp": "2024-03-02T10:50:00Z"
}
```

---

## 📚 Usage Examples

### Example 1: Complete Bounty Workflow

```bash
# 1. Get all available tasks
curl http://localhost:3000/api/tasks

# 2. Request a specific bounty
curl -X POST http://localhost:3000/api/bounties/request \
  -H "Content-Type: application/json" \
  -d '{
    "userId": "john_doe",
    "taskId": "abc-123",
    "wallet": "9B5X76QSPSLvz4YEKMHzKjK8n3RQcZhdKCdR4YYScah8"
  }'

# 3. Complete the task (user does the work)
# User completes task...

# 4. Submit completion and receive payout
curl -X POST http://localhost:3000/api/bounties/complete \
  -H "Content-Type: application/json" \
  -d '{
    "userId": "john_doe",
    "taskId": "abc-123",
    "wallet": "9B5X76QSPSLvz4YEKMHzKjK8n3RQcZhdKCdR4YYScah8",
    "proofUrl": "https://twitter.com/john_doe/status/123456789"
  }'

# 5. Check payout status
curl http://localhost:3000/api/bounties/john_doe
```

### Example 2: Using with JavaScript

```javascript
// Initialize Eliza Lobster client
const elizaApi = 'http://localhost:3000/api';

// Get available tasks
async function getTasks() {
  const response = await fetch(`${elizaApi}/tasks`);
  const data = await response.json();
  return data.data;
}

// Request a bounty
async function requestBounty(userId, taskId, wallet) {
  const response = await fetch(`${elizaApi}/bounties/request`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ userId, taskId, wallet })
  });
  return response.json();
}

// Complete bounty
async function completeBounty(userId, taskId, wallet, proofUrl) {
  const response = await fetch(`${elizaApi}/bounties/complete`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ userId, taskId, wallet, proofUrl })
  });
  return response.json();
}

// Usage
const tasks = await getTasks();
const bounty = await requestBounty('user1', tasks[0].id, 'SolanaWallet...');
const payout = await completeBounty('user1', tasks[0].id, 'SolanaWallet...', 'proof-url');
console.log('Transaction Hash:', payout.data.txHash);
```

---

## 💳 Bounty System Details

### Bounty Statuses
- **pending**: Task requested, awaiting completion
- **completed**: Task submitted by user
- **verified**: Admin verification (future feature)
- **paid**: Reward distributed on blockchain

### Task Categories
- **social**: Social media engagement (tweets, shares, follows)
- **development**: Technical tasks (contracts, dApps, deployments)
- **content**: Content creation (guides, videos, articles)

### Difficulty Levels
- **easy**: 15-60 minutes, 5-25 USDC reward
- **medium**: 1-3 hours, 25-75 USDC reward
- **hard**: 3-8 hours, 75-200+ USDC reward

### Token Details

**SOL (Solana Native Token)**
- Decimal places: 9
- Smallest unit: 1 lamport = 0.000000001 SOL
- Transaction type: SystemProgram.transfer

**USDC (Stablecoin)**
- Decimal places: 6
- Smallest unit: 0.000001 USDC
- Transaction type: SPL Token transfer
- Mint: `EPjFWaLb3K6L5ADVf3uJNekuCbHL7bo7jkXxvEz7QkS`

---

## 🔒 Security Considerations

### Private Key Management
```bash
# ✅ DO:
- Store in environment variables
- Use secure key management services
- Rotate keys periodically
- Use separate treasury wallets for different networks

# ❌ DON'T:
- Commit private keys to version control
- Share keys in chat or email
- Use same key for development and production
- Log keys in debug output
```

### Wallet Validation
```typescript
// All wallets are validated before use
function validateWallet(wallet: string): boolean {
  try {
    const publicKey = new PublicKey(wallet);
    return PublicKey.isOnCurve(publicKey.toBuffer());
  } catch {
    return false;
  }
}
```

### Transaction Security
- All transactions require keypair signature
- Confirmation required (commitment: "confirmed")
- Amount validation prevents zero transfers
- Error handling prevents partial payouts

### Best Practices
1. **Fund Wallet Carefully**: Only deposit necessary funds
2. **Monitor Transactions**: Check Solscan for all payouts
3. **Rate Limiting**: Implement in production (not included)
4. **Database**: Use persistent DB (not in-memory storage)
5. **Logging**: Audit all bounty operations
6. **Testing**: Use devnet for testing before mainnet

---

## 🚀 Deployment

### Development
```bash
npm run dev
# Server runs on http://localhost:3000
```

### Production Build
```bash
npm run build
npm start
```

### Docker Deployment
```dockerfile
FROM node:18-alpine
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build
CMD ["npm", "start"]
```

### Environment Variables for Production
```env
NODE_ENV=production
SOLANA_RPC=https://api.mainnet-beta.solana.com
TREASURY_PRIVATE_KEY=YourBase58Key
PORT=3000
```

### Deployment Platforms
- **Heroku**: ✅ Supported
- **AWS Lambda**: ⚠️ Needs serverless adapter
- **Railway.app**: ✅ Simple deployment
- **Vercel**: ✅ Serverless function
- **Self-hosted**: ✅ Docker or Node.js

---

## 📊 Monitoring & Maintenance

### Health Check
```bash
curl http://localhost:3000/health
```

### View Logs
```bash
# Development
npm run dev 2>&1 | tee logs.txt

# Production
pm2 logs eliza-lobster
```

### Metrics to Monitor
- Request latency
- Failed payouts
- Bounty completion rate
- Treasury balance
- Transaction costs (fees)

---

## 🤝 Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

---

## 📝 License

MIT License - see LICENSE file for details

---

## 🆘 Support & Troubleshooting

### Issue: "Invalid TREASURY_PRIVATE_KEY format"
**Solution**: Ensure your private key is properly Base58 encoded

### Issue: "Invalid wallet address"
**Solution**: Verify wallet address is valid Solana address (44-45 characters)

### Issue: "Payout failed: Account not found"
**Solution**: Treasury wallet needs SOL/USDC balance. Fund your treasury address

### Issue: "RPC request failed"
**Solution**: Check SOLANA_RPC endpoint is accessible and active

### Debugging
```bash
# Enable verbose logging
DEBUG=* npm run dev

# Test wallet validation
curl -X POST http://localhost:3000/api/bounties/request \
  -H "Content-Type: application/json" \
  -d '{"userId":"test","taskId":"xxx","wallet":"invalid"}'
```

---

## 📞 Contact & Resources

- **Documentation**: [Solana Docs](https://docs.solana.com)
- **Web3.js Docs**: [Web3.js API](https://docs.solana.com/developers/clients/javascript)
- **SPL Token Docs**: [SPL Token](https://spl.solana.com/token)
- **Solscan Explorer**: [https://solscan.io](https://solscan.io)

---

**Made with 🦞 & ❤️ for the Solana ecosystem**
