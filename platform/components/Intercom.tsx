import Intercom from '@intercom/messenger-js-sdk';

Intercom({
  app_id: process.env.NEXT_PUBLIC_INTERCOM_APP_ID || '',
  // user_id: user.id, // IMPORTANT: Replace "user.id" with the variable you use to capture the user's ID
  // name: user.name, // IMPORTANT: Replace "user.name" with the variable you use to capture the user's name
  // email: user.email, // IMPORTANT: Replace "user.email" with the variable you use to capture the user's email
  // created_at: user.createdAt, // IMPORTANT: Replace "user.createdAt" with the variable you use to capture the user's sign-up date in a Unix timestamp (in seconds) e.g. 1704067200
});