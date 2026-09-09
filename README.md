# IWWN New In Monitor

Checks https://www.iwonderwhatsnext.co.uk/new-in/ every 15 minutes and
emails you when new products appear. Runs for free on GitHub's servers —
your computer does not need to be on.

## One-time setup (about 10 minutes)

### 1. Create a GitHub account
Free, at github.com, if you don't already have one.

### 2. Create a new repository
- Click the **+** in the top right → **New repository**
- Name it anything, e.g. `iwwn-monitor`
- Set it to **Private** (keeps your email address out of public view)
- Click **Create repository**

### 3. Upload these files
On the new repo's page, click **Add file → Upload files**, and drag in
all the files from this folder, keeping the folder structure:
- `monitor.py`
- `requirements.txt`
- `seen_products.json`
- `.github/workflows/monitor.yml`

(If GitHub's uploader flattens the `.github` folder, instead use
**Add file → Create new file**, type `.github/workflows/monitor.yml` as
the filename — it will create the folders automatically — then paste
the contents in.)

Commit the files once uploaded.

### 4. Create a Gmail app password
This lets the script send email from a Gmail account without using your
real password.
1. Go to https://myaccount.google.com/apppasswords (use the Gmail
   account you want emails to be sent *from* — can be a new free one if
   you'd rather not use your main account)
2. You may need to enable 2-Step Verification first if it's not already on
3. Create an app password (name it "IWWN monitor")
4. Copy the 16-character password shown — you won't see it again

### 5. Add your secrets to GitHub
In your new repo: **Settings → Secrets and variables → Actions → New
repository secret**. Add three secrets:

| Name | Value |
|---|---|
| `GMAIL_ADDRESS` | the Gmail address from step 4 |
| `GMAIL_APP_PASSWORD` | the 16-character app password from step 4 |
| `RECIPIENT_EMAIL` | the email address you want alerts sent *to* (can be the same address) |

### 6. Run it once manually to test
Go to the **Actions** tab → click **Monitor IWWN New In page** on the
left → **Run workflow** → **Run workflow** button.

Wait about 30 seconds, then click into the run to see the log.
- First run: it should say "First run: recorded X existing products as
  baseline." — no email yet, this is expected, it's just learning what's
  currently on the site.
- After that, it will only email you about products that weren't there
  last time.

### 7. Done
It will now run automatically every 15 minutes, forever, for free.

## Checking it's working
- **Actions** tab shows every run and whether it succeeded or failed.
- If a run fails, click into it to see the error — the most likely
  cause is the site's page layout changing, which would need a small
  update to `monitor.py`. If that happens, send me the error text and
  I'll fix it.

## Turning it off
Delete the repository, or go to **Actions → Monitor IWWN New In page →
"..." menu → Disable workflow**.
