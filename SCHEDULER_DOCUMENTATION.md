# 📅 GitHub Actions Scheduler Documentation

## Overview

This document describes the GitHub Actions scheduler for the Mutual Fund AI Assistant project. The scheduler automates various maintenance and monitoring tasks to ensure the application runs smoothly and efficiently.

## 🚀 Scheduler Architecture

The scheduler consists of 5 main jobs that run on different schedules:

### 1. 🔄 Data Update Job
- **Schedule**: Every 6 hours (`0 */6 * * *`)
- **Purpose**: Updates mutual fund data and refreshes knowledge base
- **Actions**:
  - Checks for data changes
  - Updates fund information (NAV, expense ratios, etc.)
  - Generates update reports
  - Uploads artifacts for tracking

### 2. 🏥 Health Check Job
- **Schedule**: Every hour (`0 * * * *`)
- **Purpose**: Monitors application health and API availability
- **Actions**:
  - Tests API endpoints
  - Checks Groq API connectivity
  - Validates response times
  - Generates health reports

### 3. ✅ Data Validation Job
- **Schedule**: Every 12 hours (`0 */12 * * *`)
- **Purpose**: Validates data integrity and quality
- **Actions**:
  - Runs comprehensive data validation
  - Checks data consistency
  - Validates API responses
  - Generates validation reports

### 4. 📈 Performance Monitoring Job
- **Schedule**: Every 4 hours (`0 */4 * * *`)
- **Purpose**: Monitors system performance and response times
- **Actions**:
  - Runs performance benchmarks
  - Tests API response times
  - Monitors resource usage
  - Generates performance metrics

### 5. 📊 Weekly Report Job
- **Schedule**: Every Sunday at 9 AM UTC (`0 9 * * 0`)
- **Purpose**: Generates comprehensive weekly reports
- **Actions**:
  - Compiles weekly statistics
  - Creates performance summaries
  - Generates trend analysis
  - Sends email reports

### 6. 🧹 Cleanup Job
- **Schedule**: Weekly (runs with weekly report)
- **Purpose**: Cleans up old artifacts and logs
- **Actions**:
  - Deletes artifacts older than 30 days
  - Cleans up temporary files
  - Optimizes storage usage

## 🔧 Configuration

### Required Secrets

Add these secrets to your GitHub repository:

| Secret | Description | Required |
|--------|-------------|-----------|
| `GROQ_API_KEY` | Groq API key for AI responses | ✅ |
| `HDFC_API_KEY` | HDFC Mutual Fund API key | ✅ |
| `API_BASE_URL` | Production API base URL | ✅ |
| `EMAIL_USERNAME` | SMTP email username | ✅ |
| `EMAIL_PASSWORD` | SMTP email password | ✅ |
| `NOTIFICATION_EMAIL` | Email for notifications | ✅ |
| `CRITICAL_EMAIL` | Email for critical alerts | ✅ |

### Environment Variables

The scheduler uses these environment variables:

```yaml
env:
  GROQ_API_KEY: ${{ secrets.GROQ_API_KEY }}
  HDFC_API_KEY: ${{ secrets.HDFC_API_KEY }}
  API_BASE_URL: ${{ secrets.API_BASE_URL }}
  VALIDATION_LEVEL: 'comprehensive'
  PERFORMANCE_THRESHOLD: '2.0'
  REPORT_TYPE: 'weekly'
```

## 📋 Manual Execution

You can manually trigger any scheduler job using the GitHub Actions UI:

1. Go to your repository's Actions tab
2. Select "📅 Mutual Fund AI Assistant Scheduler" workflow
3. Click "Run workflow"
4. Choose the task type you want to run:
   - `health_check`
   - `data_update`
   - `data_validation`
   - `performance_monitoring`
   - `weekly_report`

## 📊 Monitoring and Alerts

### Health Monitoring

The health check job monitors:
- API endpoint availability
- Groq API connectivity
- Response time thresholds
- Error rates

### Performance Monitoring

The performance job tracks:
- API response times
- Memory usage
- CPU utilization
- Request throughput

### Alert Levels

- **🟢 Normal**: All systems operational
- **🟡 Warning**: Performance degradation detected
- **🔴 Critical**: System failure or critical issues

## 📁 Artifacts and Reports

### Generated Artifacts

| Job | Artifact Name | Retention Period |
|-----|---------------|------------------|
| Data Update | `data-update-report-{run_number}` | 30 days |
| Health Check | `health-check-report-{run_number}` | 7 days |
| Data Validation | `validation-report-{run_number}` | 14 days |
| Performance | `performance-report-{run_number}` | 7 days |
| Weekly Report | `weekly-report-{run_number}` | 90 days |

### Report Structure

```
reports/
├── data/
│   ├── fund_updates.json
│   ├── nav_changes.json
│   └── expense_ratios.json
├── weekly/
│   ├── summary.json
│   ├── performance_metrics.json
│   └── trends.json
└── validation/
    ├── data_quality.json
    └── consistency_checks.json
```

## 🔄 Workflow Dependencies

### Sequential Dependencies

```
Data Update → Data Validation → Health Check → Performance Monitoring
```

### Parallel Execution

- Health checks run independently
- Performance monitoring runs independently
- Weekly report depends on all other jobs

## 🚨 Troubleshooting

### Common Issues

#### 1. Workflow Not Triggering
- **Cause**: Incorrect cron expression
- **Solution**: Verify cron syntax in workflow file
- **Check**: GitHub Actions scheduler documentation

#### 2. Missing Secrets
- **Cause**: Secrets not configured in repository
- **Solution**: Add required secrets to repository settings
- **Check**: Repository → Settings → Secrets and variables

#### 3. API Timeouts
- **Cause**: Network issues or API rate limits
- **Solution**: Check API status and rate limits
- **Monitor**: Response times in performance reports

#### 4. Artifact Upload Failures
- **Cause**: File size limits or permission issues
- **Solution**: Check artifact size limits (< 2GB)
- **Monitor**: Workflow logs for error details

### Debugging Steps

1. **Check Workflow Logs**
   ```bash
   # In GitHub Actions UI
   Actions → Select workflow → View logs
   ```

2. **Verify Environment Variables**
   ```bash
   # Check if secrets are properly set
   echo $GROQ_API_KEY
   ```

3. **Test API Connectivity**
   ```bash
   # Test Groq API
   curl -H "Authorization: Bearer $GROQ_API_KEY" \
        https://api.groq.com/openai/v1/models
   ```

4. **Validate Configuration**
   ```bash
   # Check workflow syntax
   yamllint .github/workflows/scheduler_simple.yml
   ```

## 📈 Performance Optimization

### Best Practices

1. **Optimize Cron Schedules**
   - Avoid overlapping executions
   - Consider peak traffic times
   - Balance frequency vs. resource usage

2. **Resource Management**
   - Use appropriate runner sizes
   - Monitor resource consumption
   - Optimize artifact storage

3. **Error Handling**
   - Implement retry logic
   - Set appropriate timeouts
   - Monitor failure rates

### Scaling Considerations

- **Horizontal Scaling**: Multiple workflow runs
- **Vertical Scaling**: Larger runner instances
- **Queue Management**: Limit concurrent executions

## 🔒 Security Considerations

### Secret Management

- Never commit secrets to repository
- Use GitHub Secrets for sensitive data
- Rotate API keys regularly
- Monitor secret usage

### Access Control

- Limit workflow permissions
- Use least privilege principle
- Monitor workflow execution
- Audit access logs

## 📚 API Integration

### Supported APIs

1. **Groq API**
   - Purpose: AI response generation
   - Rate limits: 30 requests/minute
   - Authentication: Bearer token

2. **HDFC Mutual Fund API**
   - Purpose: Fund data retrieval
   - Rate limits: 100 requests/hour
   - Authentication: API key

### Error Handling

- Implement exponential backoff
- Handle rate limit responses
- Log API errors appropriately
- Provide fallback mechanisms

## 🌐 Deployment

### Production Deployment

1. **Enable Scheduler**
   ```bash
   # Commit workflow file
   git add .github/workflows/scheduler_simple.yml
   git commit -m "Add GitHub Actions scheduler"
   git push origin main
   ```

2. **Configure Secrets**
   - Add all required secrets
   - Test secret access
   - Validate configuration

3. **Monitor First Run**
   - Check workflow execution
   - Verify artifact generation
   - Monitor performance metrics

### Testing Environment

1. **Test Workflow Syntax**
   ```bash
   # Use GitHub Actions CLI
   act -j data_update
   ```

2. **Validate Scripts**
   ```bash
   # Test individual scripts
   python scripts/health_check.py
   python scripts/validate_data.py
   ```

## 📞 Support

### Getting Help

1. **Check Documentation**
   - Review this documentation
   - Check GitHub Actions docs
   - Review script documentation

2. **Community Support**
   - GitHub Issues
   - Stack Overflow
   - Discord/Slack channels

3. **Emergency Contacts**
   - Critical alerts: `CRITICAL_EMAIL`
   - General support: `NOTIFICATION_EMAIL`

---

## 📋 Quick Reference

### Cron Expressions

| Schedule | Cron Expression | Description |
|----------|----------------|-------------|
| Every 6 hours | `0 */6 * * *` | Data updates |
| Every hour | `0 * * * *` | Health checks |
| Every 4 hours | `0 */4 * * *` | Performance monitoring |
| Every 12 hours | `0 */12 * * *` | Data validation |
| Weekly Sunday 9AM | `0 9 * * 0` | Weekly reports |

### Workflow Commands

```bash
# Trigger specific job
curl -X POST \
  -H "Authorization: token $GITHUB_TOKEN" \
  -H "Accept: application/vnd.github.v3+json" \
  https://api.github.com/repos/owner/repo/actions/workflows/scheduler_simple.yml/dispatches \
  -d '{"ref":"main","inputs":{"task_type":"health_check"}}'
```

### Monitoring Commands

```bash
# Check workflow status
gh run list --repo owner/repo --workflow scheduler_simple.yml

# View workflow logs
gh run view --repo owner/repo --log

# Download artifacts
gh run download --repo owner/repo <run-id>
```

---

This scheduler provides comprehensive automation for the Mutual Fund AI Assistant, ensuring reliable operation, continuous monitoring, and proactive maintenance.
