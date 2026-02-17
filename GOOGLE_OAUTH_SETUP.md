# Google OAuth 2.0 Setup Guide

This app supports login and registration via Google OAuth 2.0. Follow these steps to enable it.

## 1. Create OAuth credentials in Google Cloud Console

1. Go to [Google Cloud Console](https://console.cloud.google.com/).
2. Create or select a project.
3. Navigate to **APIs & Services** → **Credentials**.
4. Click **Create Credentials** → **OAuth client ID**.
5. If prompted, configure the **OAuth consent screen** (choose External for public apps).
6. For **Application type**, select **Web application**.
7. Add the **Authorized redirect URI**:
   - Local: `http://127.0.0.1:8000/auth/google/callback/`
   - Production: `https://your-domain.com/auth/google/callback/`
8. Copy the **Client ID** and **Client Secret**.

## 2. Set environment variables

Store credentials in environment variables or a `.env` file (do **not** commit them to git):

```bash
GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-client-secret
GOOGLE_REDIRECT_URI=http://127.0.0.1:8000/auth/google/callback/
```

For production, use your real domain:

```bash
GOOGLE_REDIRECT_URI=https://your-domain.com/auth/google/callback/
```

## 3. Security notes

- The app validates the ID token `aud` (audience) against `GOOGLE_CLIENT_ID`.
- State parameter is stored in session and verified on callback to prevent CSRF.
- OAuth session keys are cleared on logout.
- Never commit `GOOGLE_CLIENT_SECRET` or similar secrets to version control.

## 4. Optional: restrict by domain

To allow only users from a specific domain (e.g. `@company.com`), add a check in `google_login_callback` in `myapp/views.py` after extracting the email:

```python
ALLOWED_EMAIL_DOMAIN = os.environ.get('GOOGLE_ALLOWED_DOMAIN', None)
if ALLOWED_EMAIL_DOMAIN and not email.endswith('@' + ALLOWED_EMAIL_DOMAIN):
    logger.warning(f"Rejected OAuth login: email domain not allowed: {email}")
    return redirect('user_login')
```
