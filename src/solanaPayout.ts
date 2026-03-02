import {
  Connection,
  Keypair,
  PublicKey,
  SystemProgram,
  Transaction,
  sendAndConfirmTransaction
} from "@solana/web3.js";
import bs58 from "bs58";

const connection = new Connection(process.env.SOLANA_RPC!, "confirmed");
const treasury = Keypair.fromSecretKey(
  bs58.decode(process.env.TREASURY_PRIVATE_KEY!)
);

export async function sendSol(wallet: string, amount: number) {
  const transaction = new Transaction().add(
    SystemProgram.transfer({
      fromPubkey: treasury.publicKey,
      toPubkey: new PublicKey(wallet),
      lamports: amount * 1e9
    })
  );

  return await sendAndConfirmTransaction(
    connection,
    transaction,
    [treasury]
  );
}