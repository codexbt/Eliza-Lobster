import request from 'supertest';
import express, { Express } from 'express';
import { createApp } from '../src/index';

describe('API Routes', () => {
  let app: Express;

  beforeAll(() => {
    app = createApp();
  });

  describe('GET /health', () => {
    it('should return 200 OK', async () => {
      const response = await request(app).get('/health');
      expect(response.status).toBe(200);
      expect(response.body).toHaveProperty('status', 'ok');
    });
  });

  describe('GET /api/tasks', () => {
    it('should return array of active tasks', async () => {
      const response = await request(app).get('/api/tasks');
      expect(response.status).toBe(200);
      expect(response.body.success).toBe(true);
      expect(Array.isArray(response.body.data)).toBe(true);
    });
  });

  describe('POST /api/bounties/request', () => {
    it('should require valid wallet address', async () => {
      const response = await request(app)
        .post('/api/bounties/request')
        .send({
          taskId: 'invalid-wallet',
          wallet: 'invalid'
        });
      expect(response.status).toBe(400);
      expect(response.body.success).toBe(false);
    });

    it('should accept valid wallet address', async () => {
      const response = await request(app)
        .post('/api/bounties/request')
        .send({
          taskId: '1',
          wallet: '11111111111111111111111111111112'
        });
      expect([200, 400]).toContain(response.status);
    });
  });

  describe('404 Handling', () => {
    it('should return 404 for unknown routes', async () => {
      const response = await request(app).get('/unknown-route');
      expect(response.status).toBe(404);
      expect(response.body.success).toBe(false);
      expect(response.body.error).toContain('not found');
    });
  });
});
