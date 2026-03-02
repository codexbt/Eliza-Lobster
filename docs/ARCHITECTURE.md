# Eliza Lobster - Architecture Documentation

## Overview

Eliza Lobster is a production-grade bounty system built on Solana blockchain infrastructure. The architecture follows clean code principles with separation of concerns, making it scalable and maintainable.

## System Architecture

```
┌─────────────────────────────────────────────────────────┐
│                   Client Applications                    │
│              (Web, Mobile, CLI Clients)                  │
└────────────────────────────┬────────────────────────────┘
                             │
                             ↓
┌─────────────────────────────────────────────────────────┐
│                   Express.js API Server                  │
│  ┌─────────────────────────────────────────────────────┐ │
│  │            Middleware Layer                          │ │
│  │  • Request Logging                                   │ │
│  │  • Error Handling                                    │ │
│  │  • CORS, Body Parsing                               │ │
│  │  • Health Checks                                     │ │
│  └─────────────────────────────────────────────────────┘ │
│                             │                            │
│  ┌─────────────────────────────────────────────────────┐ │
│  │            Routing Layer (routes.ts)                │ │
│  │  • GET /api/tasks                                   │ │
│  │  • POST /api/bounties/request                       │ │
│  │  • POST /api/bounties/complete                      │ │
│  │  • GET /api/bounties/:userId                        │ │
│  └─────────────────────────────────────────────────────┘ │
│                             │                            │
│  ┌─────────────────────────────────────────────────────┐ │
│  │         Business Logic Layer                        │ │
│  │  ┌──────────────┐  ┌──────────────┐                │ │
│  │  │ tasks.ts     │  │ solanaPayout │                │ │
│  │  │ (Task Mgmt)  │  │ (Blockchain) │                │ │
│  │  └──────────────┘  └──────────────┘                │ │
│  └─────────────────────────────────────────────────────┘ │
│                             │                            │
│  ┌─────────────────────────────────────────────────────┐ │
│  │            Type System (types.ts)                   │ │
│  │  • Task Interface                                   │ │
│  │  • Bounty Interface                                 │ │
│  │  • ApiResponse<T>                                   │ │
│  │  • PayoutResult                                     │ │
│  └─────────────────────────────────────────────────────┘ │
└─────────────────────────────┬────────────────────────────┘
                             │
         ┌───────────────────┴───────────────────┐
         ↓                                       ↓
┌──────────────────────────┐      ┌───────────────────────┐
│   Solana JSON-RPC       │      │   Configuration       │
│                          │      │  - .env variables    │
│ • Connection Pool        │      │  - task definitions   │
│ • Transaction Signing    │      │  - network settings   │
│ • Account Queries        │      └───────────────────────┘
│                          │
│ • SOL Transfers          │
│   (SystemProgram)        │
│                          │
│ • USDC Transfers         │
│   (SPL Token Program)    │
└──────────────────────────┘
         ↓
┌──────────────────────────┐
│   Solana Blockchain      │
│                          │
│ • Program Execution      │
│ • Account State          │
│ • Transaction History    │
└──────────────────────────┘
```

## Component Breakdown

### 1. Middleware Layer (`src/index.ts`)

**Responsibilities:**
- Request logging with timestamps
- Error handling and recovery
- CORS configuration
- JSON body parsing
- Health monitoring

**Key Middleware:**
- Logger: Captures all HTTP requests
- ErrorHandler: Catches exceptions and formats responses
- HealthCheck: `GET /health` endpoint
- NotFound: Handles 404 routes

### 2. Routing Layer (`src/routes.ts`)

**Responsibilities:**
- HTTP endpoint definitions
- Request validation
- Response formatting
- Route orchestration

**Endpoints:**
```
GET    /api/tasks                      → getActiveTasks()
GET    /api/tasks/:taskId              → getTaskById()
GET    /api/tasks/category/:category   → getTasksByCategory()
POST   /api/bounties/request           → createBounty()
POST   /api/bounties/complete          → completeBounty()
GET    /api/bounties/:userId           → getUserBounties()
```

### 3. Business Logic Layer

#### Tasks Module (`src/tasks.ts`)
- In-memory task storage
- Task filtering and queries
- Metadata management

**Functions:**
```typescript
getActiveTasks()              // Returns all active tasks
getTaskById(id)               // Fetch specific task
getTasksByCategory(category)  // Filter by category
getTasksByDifficulty(level)   // Filter by difficulty
```

#### Solana Payout Module (`src/solanaPayout.ts`)
- Blockchain communication
- Transaction creation
- Wallet validation
- Treasury balance checks

**Functions:**
```typescript
validateWallet(address)       // Validate Solana address
sendSol(wallet, amount)       // Transfer SOL (native)
sendUsdc(wallet, amount)      // Transfer USDC (SPL token)
checkTreasuryBalance()        // Query treasury funds
```

### 4. Type System (`src/types.ts`)

**Interfaces:**
```typescript
interface Task {
  id: string
  title: string
  description: string
  reward: number
  rewardToken: 'SOL' | 'USDC'
  category: string
  difficulty: 'easy' | 'medium' | 'hard'
  timeLimit: number
  createdAt: Date
  isActive: boolean
}

interface Bounty {
  id: string
  taskId: string
  userId: string
  wallet: string
  status: 'pending' | 'completed' | 'verified' | 'paid'
  reward: number
  transactionHash?: string
  createdAt: Date
  completedAt?: Date
  paidAt?: Date
}

interface ApiResponse<T> {
  success: boolean
  data?: T
  error?: string
  timestamp: Date
}

interface PayoutResult {
  success: boolean
  transactionHash: string
  amount: number
  token: 'SOL' | 'USDC'
  wallet: string
  timestamp: Date
}
```

## Data Flow

### 1. Task Request Flow
```
Client
  ↓
GET /api/tasks
  ↓
Router.getTasks()
  ↓
tasks.getActiveTasks()
  ↓
Format ApiResponse<Task[]>
  ↓
Return JSON
```

### 2. Bounty Completion Flow
```
Client
  ↓
POST /api/bounties/complete
  ↓
Validate Input
  ↓
Router.completeBounty()
  ↓
validateWallet()
  ↓
sendSol() or sendUsdc()
  ↓
Blockchain Transaction
  ↓
Return PayoutResult
  ↓
Update Bounty Status
  ↓
Return ApiResponse<PayoutResult>
```

## Error Handling

### Request Validation
- JSON schema validation on POST requests
- Wallet address format verification using PublicKey.isOnCurve()
- Amount range checking (min: 0.01, max: 1000)

### Transaction Handling
- Try-catch blocks on all async operations
- Middleware-level error capture
- Structured error responses with timestamps
- Logging of exceptions with stack traces

### Recovery
- Automatic retry for transient failures
- Graceful degradation if RPC unavailable
- Clear error messages for clients

## Scalability Considerations

### Current State
- In-memory task storage (suitable for ≤ 1000 tasks)
- In-memory bounty history
- Stateless HTTP servers

### Future Improvements
1. **Database Layer**
   - PostgreSQL for persistent storage
   - Indexed queries for performance
   - Transaction-safe operations

2. **Caching**
   - Redis for frequently accessed tasks
   - Response caching with TTL
   - Reduced RPC calls

3. **Queue System**
   - Bull/BullMQ for payment processing
   - Async task handling
   - Retry logic for failed transactions

4. **Load Balancing**
   - Multiple server instances
   - Load balancer (Nginx/HAProxy)
   - Database replication

## Security Architecture

### Authentication & Authorization
- (Future) JWT tokens for user identification
- Role-based access control
- API key validation (optional)

### Blockchain Security
- On-curve wallet validation before transfers
- Treasury keypair encrypted in environment
- No keys stored in code or logs
- Wallet address sanitization

### Network Security
- CORS configuration
- Rate limiting (future)
- Input validation on all endpoints
- Error message sanitization

### Data Protection
- Sensitive data in .env only
- Private keys never logged
- Transaction hashes in audit trail
- User wallet addresses pseudonymized

## Deployment Architecture

### Environment Configurations

**Development**
- Local RPC (Solana CLI)
- SQLite for data (future)
- Debug logging enabled

**Staging**
- Devnet RPC
- PostgreSQL replica
- Integration testing enabled

**Production**
- Mainnet-Beta RPC
- Redundant RPC endpoints
- Minimal logging
- Health monitoring

### Infrastructure
- Docker containerization
- Kubernetes orchestration (optional)
- Auto-scaling policies
- Load balancing
- Database replication
- Backup strategies

## Performance Metrics

### Target SLA
- API Response Time: < 500ms (p95)
- Transaction Confirmation: < 30 seconds
- System Uptime: 99.9%
- Concurrent Users: 1000+

### Monitoring
- Request latency tracking
- Error rate monitoring
- RPC endpoint health
- Treasury balance alerts
- Transaction success rates

## Maintenance & Operations

### Regular Tasks
- RPC endpoint health checks
- Treasury balance reconciliation
- Backup verification
- Dependency updates
- Security patches

### Monitoring & Alerts
- Sentry for error tracking
- Grafana for metrics visualization
- PagerDuty for incident response
- CloudWatch for AWS deployments

## Conclusion

The architecture is designed to be:
- **Scalable**: Multiple layers allow horizontal scaling
- **Maintainable**: Clear separation of concerns
- **Secure**: Multiple security checkpoints
- **Reliable**: Error handling and recovery mechanisms
- **Observable**: Comprehensive logging and monitoring

This foundation supports growth from prototype to production-grade system.
