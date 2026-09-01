# LinkedIn API setup (one-time, done by you)

This is the part I can't do for you — registering a developer app and
granting consent has to happen in your own LinkedIn login. Once it's done,
the daily pipeline can publish through the official API with no further
manual steps until the token needs renewing.

## 1. Create a LinkedIn Company Page (if you don't have one)

LinkedIn requires every Developer App to be linked to a Company Page you
administer, even for personal posting. If you don't already have one:
LinkedIn → Work icon → Create a Company Page.

## 2. Register the Developer App

1. Go to https://www.linkedin.com/developers/apps → **Create app**
2. Fill in app name, link it to your Company Page, upload a logo, agree to terms
3. LinkedIn will ask you to verify the app against the Company Page (an admin
   verification step, done in-app)

## 3. Request the products

On your app's **Products** tab, request:
- **Sign In with LinkedIn using OpenID Connect**
- **Share on LinkedIn**

These are typically self-serve/auto-approved for apps tied to a verified
company page. If LinkedIn puts "Share on LinkedIn" into manual review, that's
outside my control — it's a wait on their side.

## 4. Register the redirect URL

On the **Auth** tab, add this exact redirect URL:

```
http://localhost:8765/callback
```

## 5. Grab your Client ID and Client Secret

Also on the **Auth** tab. Keep these out of chat and out of git — they go
into environment variables only.

## 6. Run the one-time OAuth exchange

From the `linkedin-content/` folder:

```bash
LINKEDIN_CLIENT_ID=your_client_id LINKEDIN_CLIENT_SECRET=your_client_secret python3 oauth_setup.py
```

This prints a LinkedIn authorization URL — open it, log in, click **Allow**.
The script catches the redirect locally and writes `LINKEDIN_ACCESS_TOKEN`
into the gitignored `linkedin-content/.env` file. Nothing is sent anywhere
except directly between your browser/machine and LinkedIn.

The token lasts ~60 days. When it expires, just re-run `oauth_setup.py`.

## 7. Done

Once `.env` has a valid `LINKEDIN_ACCESS_TOKEN`, the daily pipeline can call
`publish.py drafts/<file>.md` to post a specific staged draft — but only
after you approve that draft in chat. Nothing auto-publishes on its own.
