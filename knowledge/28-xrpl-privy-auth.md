# XRPL Privy Auth Integration

## Overview

Privy is a web3 authentication SDK that provides email/social login with embedded wallets. It supports XRPL through embedded key management, giving users a wallet experience without seed phrases. Ideal for mainstream-user-facing XRPL applications.

---

## 1. Architecture

```
User                     App                          XRPL
  │                        │                            │
  ├─► Email/Google Login ─►│                            │
  │                        │──► Privy creates embedded  │
  │                        │    wallet (key sharded)    │
  │                        │                            │
  │◄── App loaded with ────│                            │
  │    wallet address       │                            │
  │                        │                            │
  ├─► "Send XRP" ─────────►│                            │
  │                        │──── Privy signs TX ───────►│
  │                        │◄─── TX hash ───────────────│
  │◄── Success ────────────│                            │
```

Privy shards private keys across user device, Privy HSMs, and a third share — reconstructed only during signing. Users never see seed phrases.

---

## 2. Installation

```bash
npm install @privy-io/react-auth
# Or for Next.js
npm install @privy-io/react-auth @privy-io/nextjs
```

---

## 3. Privy Provider Setup

```jsx
// app/providers.tsx (Next.js App Router)
'use client';

import { PrivyProvider } from '@privy-io/react-auth';

export function Providers({ children }) {
  return (
    <PrivyProvider
      appId={process.env.NEXT_PUBLIC_PRIVY_APP_ID}
      config={{
        loginMethods: ['email', 'google', 'twitter', 'wallet'],
        appearance: {
          theme: 'light',
          accentColor: '#0074C2',
          logo: 'https://yourapp.com/logo.png',
        },
        embeddedWallets: {
          createOnLogin: 'users-without-wallets',
          // XRPL wallet type (requires Privy XRPL support)
          defaultChain: 'xrpl',
        },
        // Support XRPL addresses
        supportedChains: ['xrpl'],
      }}
    >
      {children}
    </PrivyProvider>
  );
}
```

---

## 4. Authentication Components

```jsx
// components/AuthButton.tsx
'use client';

import { usePrivy } from '@privy-io/react-auth';

export function AuthButton() {
  const { ready, authenticated, login, logout, user } = usePrivy();

  if (!ready) return <button disabled>Loading...</button>;

  if (authenticated) {
    const wallet = user?.wallet;
    return (
      <div>
        <p>Logged in: {user.email?.address || user.google?.name}</p>
        <p>XRPL Address: {wallet?.address}</p>
        <button onClick={logout}>Logout</button>
      </div>
    );
  }

  return (
    <button onClick={login}>
      Login with Email / Social
    </button>
  );
}
```

---

## 5. XRPL Wallet via Privy

Privy's embedded wallets for XRPL work through their signing API:

```jsx
import { usePrivy, useWallets } from '@privy-io/react-auth';
import * as xrpl from 'xrpl';

function useXRPLWallet() {
  const { user, signMessage } = usePrivy();
  const { wallets } = useWallets();
  
  // Get XRPL wallet
  const xrplWallet = wallets.find(w => w.chainType === 'xrpl');
  
  const signTransaction = async (tx: object) => {
    if (!xrplWallet) throw new Error('No XRPL wallet');
    
    // Privy handles XRPL transaction signing
    const signedTx = await xrplWallet.signTransaction(tx);
    return signedTx;
  };
  
  const sendXRP = async (destination: string, amountXRP: number) => {
    const client = new xrpl.Client('wss://xrplcluster.com');
    await client.connect();
    
    const tx = await client.autofill({
      TransactionType: 'Payment',
      Account: xrplWallet!.address,
      Destination: destination,
      Amount: String(Math.floor(amountXRP * 1_000_000))
    });
    
    const signed = await signTransaction(tx);
    const result = await client.submitAndWait(signed);
    
    await client.disconnect();
    return result;
  };
  
  return {
    address: xrplWallet?.address,
    signTransaction,
    sendXRP
  };
}
```

---

## 6. Server-Side Verification

Verify Privy auth tokens server-side:

```typescript
// app/api/xrpl/route.ts
import { PrivyClient } from '@privy-io/server-auth';
import { NextRequest, NextResponse } from 'next/server';

const privy = new PrivyClient(
  process.env.PRIVY_APP_ID!,
  process.env.PRIVY_APP_SECRET!
);

export async function POST(req: NextRequest) {
  const authToken = req.headers.get('authorization')?.replace('Bearer ', '');
  
  if (!authToken) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
  }
  
  try {
    const { userId, user } = await privy.verifyAuthToken(authToken);
    
    // Get user's XRPL address
    const xrplWallet = user.linkedAccounts.find(
      a => a.type === 'wallet' && (a as any).chainType === 'xrpl'
    );
    
    const xrplAddress = xrplWallet?.address;
    
    // Process XRPL action server-side
    return NextResponse.json({
      userId,
      xrplAddress,
      message: 'Authenticated'
    });
  } catch (e) {
    return NextResponse.json({ error: 'Invalid token' }, { status: 401 });
  }
}
```

---

## 7. No Seed Phrase UX Pattern

```jsx
// Full onboarding flow with no seed phrase mention
function OnboardingFlow() {
  const { login, authenticated, user } = usePrivy();
  const { sendXRP } = useXRPLWallet();
  const [step, setStep] = useState(0);

  const steps = [
    {
      title: 'Create your account',
      content: (
        <div>
          <p>Sign in with your email — no wallet needed.</p>
          <button onClick={login}>Get Started</button>
        </div>
      )
    },
    {
      title: 'Your wallet is ready',
      content: (
        <div>
          <p>We created a secure wallet for you automatically.</p>
          <p>Your address: {user?.wallet?.address}</p>
          <button onClick={() => setStep(2)}>Next</button>
        </div>
      )
    },
    {
      title: 'Fund your wallet',
      content: (
        <div>
          <p>Send XRP to your address to get started.</p>
          <p><strong>{user?.wallet?.address}</strong></p>
          {/* QR code here */}
        </div>
      )
    }
  ];

  useEffect(() => {
    if (authenticated) setStep(1);
  }, [authenticated]);

  return (
    <div>
      <h2>{steps[step].title}</h2>
      {steps[step].content}
    </div>
  );
}
```

---

## 8. Token Trust Line via Privy

```jsx
async function optInToToken(currency: string, issuer: string) {
  const { signTransaction } = useXRPLWallet();
  const client = new xrpl.Client('wss://xrplcluster.com');
  await client.connect();
  
  const tx = await client.autofill({
    TransactionType: 'TrustSet',
    Account: address,
    LimitAmount: {
      currency,
      issuer,
      value: '1000000'
    }
  });
  
  const signed = await signTransaction(tx);
  const result = await client.submitAndWait(signed);
  await client.disconnect();
  return result;
}
```

---

## 9. Privy Config Reference

```typescript
// Full Privy config for XRPL app
const privyConfig = {
  appId: 'clxxxxxxxxxxxxxxxx',
  config: {
    // Auth methods
    loginMethods: [
      'email',
      'google',
      'twitter',
      'discord',
      'wallet'  // external wallets (Metamask, etc.)
    ],
    
    // Appearance
    appearance: {
      theme: 'dark',
      accentColor: '#0074C2',
      logo: '/logo.png',
      landingHeader: 'Sign in to XRPL App',
      loginMessage: 'Welcome to the future of finance'
    },
    
    // Embedded wallets
    embeddedWallets: {
      createOnLogin: 'users-without-wallets',
      requireUserPasswordOnCreate: false,  // no password needed
      noPromptOnSignature: false           // show signing prompts
    },
    
    // Legal
    legal: {
      termsAndConditionsUrl: 'https://yourapp.com/terms',
      privacyPolicyUrl: 'https://yourapp.com/privacy'
    },
    
    // MFA
    mfa: {
      noPromptOnMfaRequired: false
    }
  }
};
```

---

## 10. Key Differences: Privy vs Xaman

| Feature | Privy | Xaman |
|---------|-------|-------|
| User UX | Web2-like (email login) | Crypto-native (seed) |
| Seed phrase | Hidden (sharded) | Visible |
| Mobile app | No separate app | Required |
| QR signing | No | Yes |
| Web integration | SDK (React) | REST API |
| Push notifications | No | Yes |
| Best for | Mainstream users | Crypto-native users |
| Key custody | Shared (Privy + user) | Full self-custody |

---

## 11. Security Considerations

- Privy's key sharding: 3 shares — user device, Privy HSM, recovery share
- Privy cannot sign transactions without user cooperation
- Recovery available via email/social account
- No single point of failure
- For maximum security: export private key → self-custody
- Server-side: always verify Privy auth token before trusting claimed address

---

## Related Files

- `knowledge/26-xrpl-xaman-deeplink.md` — Xaman deep-link signing
- `knowledge/27-xrpl-joey-wallet.md` — Joey developer wallet
- `knowledge/53-xrpl-wallets-auth.md` — wallet auth patterns
