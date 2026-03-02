#!/bin/bash

# Eliza Lobster - Wallet Setup Script
# This script helps set up a Solana wallet for the treasury

set -e

echo "╔════════════════════════════════════════╗"
echo "║   Eliza Lobster - Wallet Setup         ║"
echo "╚════════════════════════════════════════╝"
echo

# Check if solana CLI is installed
if ! command -v solana &> /dev/null; then
    echo "❌ Solana CLI not found. Installing..."
    sh -c "$(curl -sSfL https://release.solana.com/v1.18.0/install)"
    export PATH="/root/.local/share/solana/install/active_deployment/bin:$PATH"
else
    echo "✅ Solana CLI found"
fi

echo

# Ask for network
echo "Select Solana network:"
echo "1) Devnet (recommended for testing)"
echo "2) Mainnet Beta (production)"
echo "3) Testnet"
read -p "Enter choice (1-3): " network_choice

case $network_choice in
    1)
        NETWORK="devnet"
        RPC_URL="https://api.devnet.solana.com"
        ;;
    2)
        NETWORK="mainnet-beta"
        RPC_URL="https://api.mainnet-beta.solana.com"
        ;;
    3)
        NETWORK="testnet"
        RPC_URL="https://api.testnet.solana.com"
        ;;
    *)
        echo "Invalid choice. Using devnet."
        NETWORK="devnet"
        RPC_URL="https://api.devnet.solana.com"
        ;;
esac

echo "Using network: $NETWORK"
echo "RPC URL: $RPC_URL"
echo

# Set up Solana CLI config
echo "Setting up Solana CLI configuration..."
solana config set --url "$RPC_URL"
echo "✅ Configuration updated"
echo

# Generate new keypair
echo "Generating new keypair..."
read -p "Enter keypair file path (default: ~/.config/solana/id.json): " keypair_path
keypair_path=${keypair_path:-~/.config/solana/id.json}

solana-keygen new --no-bip39-passphrase -o "$keypair_path"
echo "✅ Keypair generated at: $keypair_path"
echo

# Get public key
echo "Setting up default keypair..."
solana config set --keypair "$keypair_path"
PUBKEY=$(solana address)
echo "✅ Default keypair set"
echo "Public Key (Wallet Address): $PUBKEY"
echo

# Get private key in Base58 format
echo "Extracting private key..."
PRIVATE_KEY_B58=$(solana config get | grep "Keypair Path" | awk '{print $NF}' | xargs cat | jq -r '.[] | @base64d' | od -An -td1 | head -1 | tr -d ' ' | python3 -c "
import sys
import base58
data = [int(x) for x in sys.stdin.read().strip().split()]
print(base58.b58encode(bytes(data[:32])).decode())
")

echo "✅ Private key extracted (first 10 chars): ${PRIVATE_KEY_B58:0:10}..."
echo

# Request airdrop for devnet
if [ "$NETWORK" = "devnet" ]; then
    echo "Requesting airdrop for development..."
    solana airdrop 5 "$PUBKEY"
    echo "✅ Airdrop requested"
    echo
fi

# Display setup instructions
echo "╔════════════════════════════════════════╗"
echo "║         Setup Complete! 🎉             ║"
echo "╚════════════════════════════════════════╝"
echo
echo "Your wallet is ready! Add these to your .env file:"
echo
echo "SOLANA_RPC=$RPC_URL"
echo "TREASURY_PRIVATE_KEY=$PRIVATE_KEY_B58"
echo
echo "Public Address: $PUBKEY"
echo
echo "Next steps:"
echo "1. Create a .env file in the project root"
echo "2. Add the values above"
echo "3. Run: npm install"
echo "4. Run: npm start"
echo
echo "For more details, see: GETTING_STARTED.md"
