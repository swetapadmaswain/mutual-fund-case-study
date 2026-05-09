
# 🚀 Quick Start Guide

## 1. Configure GitHub Secrets
Visit: https://github.com/swetapadmaswain/mutual-fund-case-study/settings/secrets/actions

Add these secrets:
- GROQ_API_KEY (your Groq API key)
- HDFC_API_KEY (your HDFC API key)  
- API_BASE_URL (https://api.groq.com/openai/v1)
- EMAIL_USERNAME (your Gmail address)
- EMAIL_PASSWORD (Gmail app password)
- NOTIFICATION_EMAIL (email for notifications)
- CRITICAL_EMAIL (email for critical alerts)

## 2. Test Scheduler
1. Go to: https://github.com/swetapadmaswain/mutual-fund-case-study/actions
2. Click "📅 Mutual Fund AI Assistant Scheduler"
3. Click "Run workflow"
4. Select "health_check" and run it

## 3. Monitor Execution
- Check workflow logs for any errors
- Verify artifacts are uploaded
- Monitor email notifications

## 4. Verify Scheduled Runs
Scheduler will automatically run:
- Every hour: Health checks
- Every 4 hours: Performance monitoring
- Every 6 hours: Data updates
- Every 12 hours: Data validation
- Every Sunday 9AM UTC: Weekly reports + cleanup

## 5. Troubleshooting
- Check workflow logs for error details
- Verify all secrets are correctly configured
- Ensure API keys are valid and have proper permissions
- Check email configuration for notification issues

📚 For detailed documentation, see:
- SCHEDULER_DOCUMENTATION.md
- GITHUB_SECRETS_SETUP.md
