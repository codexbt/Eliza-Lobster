# Security Guidelines - Eliza Lobster

## Overview

Security is a top priority for Eliza Lobster. This document outlines best practices for secure deployment, operation, and usage.

## Environment Security

### Private Key Management

**CRITICAL: Never commit private keys to git!**

1. **Storage**
   ```bash
   # Store in .env file (not in git)
   TREASURY_PRIVATE_KEY=your_base58_encoded_key
   
   # Add .env to .gitignore
   echo ".env" >> .gitignore
   ```

2. **Generation**
   ```bash
   # Use Solana CLI to generate secure keypair
   solana-keygen new --no-bip39-passphrase
   
   # Extract private key (keep secure)
   solana config get
   ```

3. **Access Control**
   - Restrict file permissions: `chmod 600 .env`
   - Use environment variables in deployment
   - Rotate keys regularly
   - Use separate keys for different environments

### RPC Endpoint Security

- Use HTTPS only
- Consider rate-limited RPC endpoints
- Monitor for unusual activity
- Backup RPC endpoints for redundancy

```env
# Good: Authenticated RPC
SOLANA_RPC=https://api-key@rpc.solana.com

# Better: Multiple endpoints with fallback
PRIMARY_RPC=https://api.mainnet-beta.solana.com
BACKUP_RPC=https://backup-rpc.example.com
```

## Wallet Validation

### Address Format Validation

All wallet addresses are validated using Solana's `PublicKey.isOnCurve()`:

```typescript
import { PublicKey } from '@solana/web3.js';

function validateWallet(wallet: string): boolean {
  try {
    const pubkey = new PublicKey(wallet);
    return PublicKey.isOnCurve(pubkey.toBuffer());
  } catch {
    return false;
  }
}
```

### Verification Checklist
- [ ] Address format is valid Base58
- [ ] Address passes on-curve check
- [ ] Address is not the system program
- [ ] Address ownership verified (for sensitive ops)

## Transaction Security

### Payout Validation

Before sending any payout:

1. **Amount Validation**
   ```typescript
   const MIN_AMOUNT = 0.01;
   const MAX_AMOUNT = 1000;
   
   if (amount < MIN_AMOUNT || amount > MAX_AMOUNT) {
     throw new Error('Invalid amount');
   }
   ```

2. **Wallet Validation**
   ```typescript
   validateWallet(recipientAddress);
   ```

3. **Balance Check**
   ```typescript
   const balance = await checkTreasuryBalance();
   if (balance < amount) {
     throw new Error('Insufficient treasury balance');
   }
   ```

4. **Rate Limiting**
   - Max transactions per hour per wallet
   - Daily treasury spend limits
   - Single transaction size limits

### Transaction Confirmation

```typescript
const signature = await sendAndConfirmTransaction(
  connection,
  transaction,
  [signer],
  {
    commitment: 'confirmed',
    maxRetries: 3
  }
);
```

## API Security

### Input Validation

All user inputs are validated:

```typescript
// Example: Bounty request validation
const validateBountyRequest = (req: Request): boolean => {
  const { taskId, wallet } = req.body;
  
  // Check required fields
  if (!taskId || !wallet) {
    throw new Error('Missing required fields');
  }
  
  // Validate formats
  if (!isValidTaskId(taskId)) {
    throw new Error('Invalid task ID');
  }
  
  if (!validateWallet(wallet)) {
    throw new Error('Invalid wallet address');
  }
  
  return true;
};
```

### Error Responses

Never expose sensitive information in error messages:

```typescript
// Bad: Leaks internal details
{
  "error": "Database connection failed at 192.168.1.1:5432"
}

// Good: Generic message
{
  "error": "Request processing failed. Please try again later."
}
```

### CORS Configuration

```typescript
const corsOptions = {
  origin: process.env.ALLOW_ORIGINS?.split(',') || [],
  credentials: true,
  methods: ['GET', 'POST', 'PUT', 'DELETE'],
  optionsSuccessStatus: 200
};
```

## Deployment Security

### Docker Security

```dockerfile
# Use minimal base image
FROM node:18-alpine

# Run as non-root user
RUN addgroup -g 1001 -S nodejs
RUN adduser -S nodejs -u 1001
USER nodejs

# Don't store secrets in image
# Use environment variables or secrets management
```

### Environment Configuration

```bash
# Never log sensitive data
# Review logs before sharing
grep -v "PRIVATE_KEY\|SECRET\|TOKEN" logs/app.log

# Use secrets management in production
# AWS Secrets Manager, HashiCorp Vault, etc.
```

### Network Security

- Use VPC/private networks for internal communication
- Whitelist IP addresses for database access
- Use firewalls to restrict access
- Enable DDoS protection
- Monitor unusual traffic patterns

## Monitoring & Alerts

### Suspicious Activity

Monitor for:
- Unusually large payouts
- Rapid successive requests from same wallet
- Invalid wallet addresses (brute force attempts)
- RPC errors or connection failures
- Treasury balance anomalies

### Alerting

```typescript
// Example: Alert on large payout
if (amount > 100) {
  logger.warn(`Large payout detected: ${amount} ${token} to ${wallet}`);
  // Send alert to admin
}

// Example: Rate limiting alert
if (requestCount > 100 && timeWindow < 60000) {
  logger.warn(`Rate limit exceeded from ${ip}`);
  // Block/throttle requests
}
```

## Incident Response

### If Private Key is Compromised

1. **Immediately**
   - Stop accepting new transactions
   - Notify users/admins
   - Document incident details

2. **Within 1 hour**
   - Generate new keypair
   - Transfer remaining funds to new wallet
   - Update environment variables

3. **Within 24 hours**
   - Post-mortem analysis
   - Security audit
   - Client notification

### If RPC is Compromised

1. Switch to backup RPC immediately
2. Verify transaction integrity
3. Re-execute failed transactions if needed
4. Audit transaction history

## Compliance

### Data Privacy

- User wallet addresses are pseudonymous
- No personally identifiable information stored
- Comply with data retention policies
- Clear data after bounty completion (optional)

### Blockchain Transparency

- All transactions are on-chain and public
- Users can verify payouts independently
- Transaction hashes stored for audit trail
- Immutable record of all bounties

### Legal Considerations

- Consult legal counsel for your jurisdiction
- Ensure bounty rewards comply with local regulations
- Terms of service for users
- Privacy policy for data handling

## Security Checklist

### Before Deployment

- [ ] Private keys stored securely (.env, not in git)
- [ ] RPC endpoints validated and tested
- [ ] Input validation on all endpoints
- [ ] Error handling doesn't leak information
- [ ] CORS configured appropriately
- [ ] Rate limiting implemented
- [ ] Health checks enabled
- [ ] Logging configured (sensitive data excluded)
- [ ] Environment variables documented
- [ ] Firewall rules configured
- [ ] SSL/TLS certificates valid
- [ ] Dependencies audited for vulnerabilities

### Regular Audits

- [ ] Monthly security review
- [ ] Quarterly dependency updates
- [ ] Annual penetration testing
- [ ] Incident log review
- [ ] Access control review
- [ ] Backup integrity testing

### Monitoring

- [ ] Error tracking (Sentry)
- [ ] Performance monitoring (New Relic/DataDog)
- [ ] Blockchain monitoring (Solscan)
- [ ] Log aggregation (ELK/Splunk)
- [ ] Alert rules configured
- [ ] On-call rotation established

## Resources

- [Solana Security Best Practices](https://docs.solana.com/developing/programming-model/transactions#security)
- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [Node.js Security Best Practices](https://nodejs.org/en/docs/guides/security/)
- [Blockchain Security](https://blog.chainalysis.com/reports/)

## Contact Security Issues

If you discover a security vulnerability:

1. **Do NOT** create a public GitHub issue
2. Email: security@example.com
3. Include reproduction steps
4. Wait for confirmation before public disclosure

Thank you for helping keep Eliza Lobster secure! 🔒
