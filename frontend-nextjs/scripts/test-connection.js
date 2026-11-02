#!/usr/bin/env node

/**
 * Test script to verify backend API and WebSocket connectivity
 */

const http = require('http');
const WebSocket = require('ws');

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
const WS_URL = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000';

console.log('🧪 Testing Agent Integration Hub Backend Connection\n');
console.log(`API URL: ${API_URL}`);
console.log(`WebSocket URL: ${WS_URL}\n`);

// Test 1: Health Check
console.log('1️⃣ Testing Health Endpoint...');
const healthUrl = new URL('/health', API_URL);
const req = http.get(healthUrl, (res) => {
  let data = '';
  res.on('data', (chunk) => {
    data += chunk;
  });
  res.on('end', () => {
    try {
      const health = JSON.parse(data);
      console.log('✅ Health check passed:', health);
      
      if (health.status === 'healthy') {
        console.log('   Status: Healthy');
        console.log(`   Redis: ${health.redis}`);
      }
    } catch (e) {
      console.log('❌ Failed to parse health response:', e.message);
      process.exit(1);
    }
  });
});

req.on('error', (error) => {
  console.log('❌ Health check failed:', error.message);
  console.log('\n💡 Make sure the backend is running:');
  console.log('   uvicorn backend.api.main:app --reload --port 8000');
  process.exit(1);
});

// Test 2: WebSocket Connection with the operator session cookie
async function testWebSocket() {
  console.log('\n2️⃣ Testing WebSocket Connection...');
  const username = process.env.OPERATOR_USERNAME;
  const password = process.env.OPERATOR_LOGIN_PASSWORD;
  if (!username || !password) {
    throw new Error('Set OPERATOR_USERNAME and OPERATOR_LOGIN_PASSWORD for this local connection check');
  }

  const login = await fetch(`${API_URL}/api/v1/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username, password }),
  });
  if (!login.ok) throw new Error(`Operator login failed (${login.status})`);
  const setCookie = login.headers.get('set-cookie') || '';
  const sessionCookie = setCookie.match(/hub_session=[^;,]+/);
  const csrfCookie = setCookie.match(/hub_csrf=[^;,]+/);
  if (!sessionCookie || !csrfCookie) throw new Error('Login response did not include session cookies');

  await new Promise((resolve, reject) => {
    const ws = new WebSocket(`${WS_URL}/ws`, {
      headers: {
        Cookie: `${sessionCookie[0]}; ${csrfCookie[0]}`,
        Origin: process.env.FRONTEND_ORIGIN || 'http://localhost:3000',
      },
    });
    const timeout = setTimeout(() => reject(new Error('WebSocket ping timed out')), 5000);
    ws.on('open', () => ws.send(JSON.stringify({ type: 'ping' })));
    ws.on('message', (data) => {
      const message = JSON.parse(data.toString());
      if (message.type === 'pong') {
        clearTimeout(timeout);
        ws.close();
        resolve();
      }
    });
    ws.on('error', reject);
  });
  console.log('✅ Session-authenticated WebSocket ping passed');
}

testWebSocket().then(() => {
  console.log('\n✅ All tests passed! Backend is ready.');
  process.exit(0);
}).catch((error) => {
  console.error('❌ WebSocket check failed:', error.message);
  process.exit(1);
});
