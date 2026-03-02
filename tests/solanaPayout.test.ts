import { validateWallet } from '../src/solanaPayout';
import { PublicKey } from '@solana/web3.js';

describe('Solana Payout Module', () => {
  describe('validateWallet', () => {
    it('should accept valid Solana addresses', () => {
      const validAddresses = [
        '11111111111111111111111111111112',
        'TokenkegQfeZyiNwAJsyFbPNKwm4SNu3Z9c4vBSk2cV',
        '4uQeVj5tqViQh7yWWGStvkEG1Zmhx6uasJtWCJziofM'
      ];

      validAddresses.forEach(addr => {
        expect(() => validateWallet(addr)).not.toThrow();
      });
    });

    it('should reject invalid addresses', () => {
      const invalidAddresses = [
        'not-a-wallet',
        '123',
        '',
        'invalid@#$%'
      ];

      invalidAddresses.forEach(addr => {
        expect(() => validateWallet(addr)).toThrow();
      });
    });

    it('should handle null/undefined', () => {
      expect(() => validateWallet(null as any)).toThrow();
      expect(() => validateWallet(undefined as any)).toThrow();
    });
  });
});
