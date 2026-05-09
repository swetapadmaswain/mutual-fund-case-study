# 🔐 GitHub Secrets Configuration Guide

## Overview

This guide provides step-by-step instructions for configuring the required GitHub secrets for the Mutual Fund AI Assistant scheduler.

## 📋 Required Secrets

| Secret Name | Description | Example Value | Priority |
|-------------|-------------|---------------|----------|
| `GROQ_API_KEY` | Groq AI API key for responses | `gsk_...` | 🔴 Critical |
| `HDFC_API_KEY` | HDFC Mutual Fund API key | `hdfc_...` | 🔴 Critical |
| `API_BASE_URL` | Production API base URL | `https://api.example.com` | 🔴 Critical |
| `EMAIL_USERNAME` | SMTP email username | `your-email@gmail.com` | 🟡 Important |
| `EMAIL_PASSWORD` | SMTP email password | `your-app-password` | 🟡 Important |
| `NOTIFICATION_EMAIL` | Email for notifications | `alerts@example.com` | 🟡 Important |
| `CRITICAL_EMAIL` | Email for critical alerts | `emergency@example.com` | 🟡 Important |

## 🚀 Setup Instructions

### Step 1: Navigate to Repository Settings

1. Go to your repository: https://github.com/swetapadmaswain/mutual-fund-case-study
2. Click on **Settings** tab
3. In the left sidebar, click **Secrets and variables** → **Actions**

### Step 2: Add Repository Secrets

Click **New repository secret** and add each secret:

#### 🔴 Critical Secrets

**GROQ_API_KEY:**
- Name: `GROQ_API_KEY`
- Value: Your Groq API key (starts with `gsk_`)
- Description: `Groq AI API key for generating responses`

**HDFC_API_KEY:**
- Name: `HDFC_API_KEY`
- Value: Your HDFC Mutual Fund API key
- Description: `HDFC Mutual Fund API key for data retrieval`

**API_BASE_URL:**
- Name: `API_BASE_URL`
- Value: `https://api.groq.com/openai/v1`
- Description: `Base URL for API endpoints`

#### 🟡 Important Secrets

**EMAIL_USERNAME:**
- Name: `EMAIL_USERNAME`
- Value: Your Gmail address
- Description: `SMTP username for email notifications`

**EMAIL_PASSWORD:**
- Name: `EMAIL_PASSWORD`
- Value: Gmail App Password (not regular password)
- Description: `SMTP password for email notifications`

**NOTIFICATION_EMAIL:**
- Name: `NOTIFICATION_EMAIL`
- Value: Email address for regular notifications
- Description: `Email address for scheduler notifications`

**CRITICAL_EMAIL:**
- Name: `CRITICAL_EMAIL`
- Value: Email address for critical alerts
- Description: `Email address for critical system alerts`

## 📧 Gmail App Password Setup

If using Gmail for notifications:

1. Enable 2-Factor Authentication on your Gmail account
2. Go to Google Account settings → Security
3. Click on **App passwords**
4. Generate a new app password
5. Use this app password (not your regular password) for `EMAIL_PASSWORD`

## 🔍 Verification Steps

### Step 3: Verify Secrets Configuration

1. After adding all secrets, verify they appear in the list
2. Ensure no typos in secret names
3. Test with a small workflow first

### Step 4: Test Scheduler

1. Go to **Actions** tab in your repository
2. Select "📅 Mutual Fund AI Assistant Scheduler"
3. Click **Run workflow**
4. Choose `health_check` as task type
5. Monitor the run for any secret-related errors

## ⚠️ Security Best Practices

### Do:
- ✅ Use strong, unique passwords
- ✅ Rotate API keys regularly
- ✅ Use app passwords instead of regular passwords
- ✅ Limit secret access to necessary repositories
- ✅ Monitor secret usage

### Don't:
- ❌ Commit secrets to repository
- ❌ Share secrets in plain text
- ❌ Use production secrets in development
- ❌ Reuse passwords across services
- ❌ Log secret values in workflows

## 🔄 Secret Rotation

### Recommended Rotation Schedule:
- **API Keys**: Every 90 days
- **Email Passwords**: Every 180 days
- **Critical Secrets**: Immediately if compromised

### Rotation Process:
1. Generate new secret
2. Update in GitHub repository settings
3. Test with new secret
4. Delete old secret from external service
5. Monitor for any issues

## 🚨 Troubleshooting

### Common Issues:

**Secret Not Found Error:**
```
Error: Required secret GROQ_API_KEY not found
```
**Solution**: Verify secret name matches exactly (case-sensitive)

**Invalid API Key:**
```
Error: 401 Unauthorized
```
**Solution**: Check API key validity and permissions

**Email Authentication Failed:**
```
Error: SMTP authentication failed
```
**Solution**: Use Gmail app password, enable 2FA

**Workflow Permission Denied:**
```
Error: Permission denied
```
**Solution**: Enable Actions in repository settings

### Debug Commands:

```bash
# Check if Actions are enabled
gh api repos/:owner/:repo/actions/permissions

# List repository secrets
gh secret list -R swetapadmaswain/mutual-fund-case-study

# Test workflow manually
gh workflow run scheduler.yml -f task_type=health_check
```

## 📊 Monitoring Secret Usage

### GitHub Actions Dashboard:
- Monitor workflow runs for secret usage
- Check for failed authentication attempts
- Review audit logs regularly

### Alert Setup:
- Configure email alerts for failed runs
- Monitor API rate limits
- Track unusual activity patterns

## 🔄 Environment-Specific Secrets

For different environments (dev/staging/prod):

### Option 1: Environment-Specific Secrets
- Create separate environments in GitHub
- Add secrets to each environment
- Use environment-specific workflows

### Option 2: Secret Naming Convention
```
DEV_GROQ_API_KEY
PROD_GROQ_API_KEY
STAGING_GROQ_API_KEY
```

## 📱 Mobile Setup

### GitHub Mobile App:
1. Install GitHub mobile app
2. Enable notifications for repository
3. Monitor workflow runs on-the-go
4. Quick access to emergency actions

## 🎯 Quick Checklist

Before deploying scheduler:

- [ ] All 7 secrets configured
- [ ] API keys tested and valid
- [ ] Email authentication working
- [ ] 2FA enabled on email accounts
- [ ] App passwords generated
- [ ] Test workflow run successful
- [ ] Monitoring alerts configured
- [ ] Documentation updated
- [ ] Team members notified

## 📞 Support

### If you encounter issues:

1. **GitHub Documentation**: https://docs.github.com/en/actions/security-guides
2. **API Provider Support**: Groq, HDFC API documentation
3. **Email Provider Support**: Gmail/SMTP setup guides
4. **Community Support**: GitHub Issues, Stack Overflow

### Emergency Contacts:
- **Critical Issues**: Check `CRITICAL_EMAIL` configuration
- **General Issues**: Check `NOTIFICATION_EMAIL` configuration

---

## ✅ Configuration Complete

Once all secrets are configured and tested, your scheduler will be fully operational and ready to automate your Mutual Fund AI Assistant maintenance tasks!
