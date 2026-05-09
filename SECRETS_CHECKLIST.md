# 🔐 GitHub Secrets Configuration Checklist

## 📋 Required Secrets (Add these 5 for now)

### 1. GROQ_API_KEY
- **Value**: `gsk_your_actual_groq_key_here`
- **Source**: https://console.groq.com/keys
- **Priority**: 🔴 Critical

### 2. API_BASE_URL
- **Value**: `https://api.groq.com/openai/v1`
- **Source**: (copy this exactly)
- **Priority**: 🔴 Critical

### 3. EMAIL_USERNAME
- **Value**: `your-email@gmail.com`
- **Source**: Your Gmail address
- **Priority**: 🟡 Important

### 4. EMAIL_PASSWORD
- **Value**: `your-16-char-app-password`
- **Source**: Gmail App Password
- **Priority**: 🟡 Important

### 5. NOTIFICATION_EMAIL
- **Value**: `alerts@your-domain.com`
- **Source**: Email for notifications
- **Priority**: 🟡 Important

## ⚙️ Setup Instructions

### Step 1: Get Groq API Key
1. Go to https://console.groq.com/keys
2. Create account if needed
3. Copy API key (starts with `gsk_`)

### Step 2: Setup Gmail App Password
1. Enable 2FA on Gmail
2. Go to https://myaccount.google.com/apppasswords
3. Select "Mail" → "Other (Custom name)"
4. Copy 16-character password

### Step 3: Add Secrets to GitHub
1. Visit: https://github.com/swetapadmaswain/mutual-fund-case-study/settings/secrets/actions
2. Click "New repository secret"
3. Add each secret from the list above

### Step 4: Skip These For Now
- **HDFC_API_KEY**: Not needed (scripts use web scraping)
- **CRITICAL_EMAIL**: Optional (use same as NOTIFICATION_EMAIL)

## ✅ Verification Checklist

Before testing scheduler:

- [ ] GROQ_API_KEY configured
- [ ] API_BASE_URL configured  
- [ ] EMAIL_USERNAME configured
- [ ] EMAIL_PASSWORD configured
- [ ] NOTIFICATION_EMAIL configured
- [ ] All secret names are exact (case-sensitive)
- [ ] No typos in secret values

## 🧪 Test After Configuration

Once secrets are configured:

1. Go to Actions tab in GitHub
2. Select "📅 Mutual Fund AI Assistant Scheduler"
3. Click "Run workflow"
4. Choose "health_check" task
5. Monitor execution

## 📧 Email Test

After first successful run:
- Check if notification emails work
- Verify email delivery
- Check spam folder if needed

---

**Ready to test once all 5 secrets are configured!**
