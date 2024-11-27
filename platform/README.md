# phospho platform

This is a React webapp

## Env

Create a `.env` in this folder `platform` :

```bash
GCP_PROJECT_ID=portal-385519
GCP_SERVICEACCOUNT_EMAIL=upload-test@portal-385519.iam.gserviceaccount.com
GCP_PRIVATE_KEY=-----BEGIN PRIVATE KEY-----

APP_ENV=local

API_VERSION=v0
NEXT_PUBLIC_API_VERSION=v0

NEXT_PUBLIC_API_URL=http://127.0.0.1:8000
#NEXT_PUBLIC_API_URL=https://api.phospho.ai

LOCAL_API_URL=http://127.0.0.1:8000
NEXT_PUBLIC_LOCAL_API_URL=http://127.0.0.1:8000
# NEXT_PUBLIC_LOCAL_API_URL=https://api.phospho.ai

# TEST_API_URL=https://staging-phospho-backend-zxs3h5fuba-ew.a.run.app
# PROD_API_URL=https://phospho-backend-zxs3h5fuba-ew.a.run.app

# Test only
NEXT_PUBLIC_AUTH_URL=https://80082208909.propelauthtest.com
PROPELAUTH_API_KEY=
PROPELAUTH_REDIRECT_URI=http://localhost:3000/api/auth/callback
PROPELAUTH_VERIFIER_KEY=-----BEGIN PUBLIC KEY-----
```

## Install dependencies

Using Node 20.17

Install the depedencies of the app with:

```
npm i
```

## Getting Started

Launch the platform server with:

```bash
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) with the **Chrome** browser to see the result.
WARNING !!! This will not work on Safari !

## Learn More

To learn more about Next.js, take a look at the following resources:

- [Next.js Documentation](https://nextjs.org/docs) - learn about Next.js features and API.
- [Learn Next.js](https://nextjs.org/learn) - an interactive Next.js tutorial.

You can check out [the Next.js GitHub repository](https://github.com/vercel/next.js/) - your feedback and contributions are welcome!
