# Task 1: Automated S3 Bucket Cleanup (Objects Older Than 30 Days)

## 1. Objective
Automate deletion of stale objects (older than 30 days) in an S3 bucket using
AWS Lambda and Boto3, avoiding reliance on manual cleanup or S3 Lifecycle Rules
where conditional/custom logic is needed.

## 2. Architecture
- **S3 Bucket**: `datson-lambda-cleanup-test` — stores test objects
- **Lambda Function**: `s3-bucket-cleanup` (Python 3.12, Boto3)
- **IAM Role**: `lambda-s3-cleanup-role` — least-privilege inline policy
- **Trigger**: Manual invocation (can be scheduled via EventBridge for production use)

Flow: Manual Invoke → Lambda → Lists objects (paginated) → Compares LastModified
vs. cutoff → Deletes stale objects → Logs results to CloudWatch

## 3. IAM Policy
Inline policy attached to `lambda-s3-cleanup-role`, scoped to a single bucket:
- `s3:ListBucket`
- `s3:DeleteObject`

See [`iam_policy.json`](./iam_policy.json) for the exact policy used.

## 4. Steps Followed
1. Created S3 bucket `datson-lambda-cleanup-test` in us-east-1
2. Uploaded architecture.png and git_commit.txt test files to the bucket
3. Created IAM role with least-privilege inline policy scoped to the bucket ARN
4. Created Lambda function (Python 3.12) with the IAM role attached
5. Wrote Boto3 code using a paginator to list all objects, compared
   timezone-aware `LastModified` against a UTC cutoff, and deleted matches
6. Used environment variables (`BUCKET_NAME`, `AGE_THRESHOLD_MINUTES`) to
   toggle between a fast test threshold and the 30-day production threshold
7. Deployed and tested with a 2-minute threshold to confirm deletion logic
   worked before switching to 30 days for the final version

## 5. Testing & Results
- Ran a manual test invocation with `AGE_THRESHOLD_MINUTES=2`
- Confirmed architecture.png and git_commit.txt older than the threshold of 2 minutes were deleted
- Verified only newer files remained in the bucket afterward
- Switched threshold back to 30 days (default) for production use
- Screenshots: `01-iam-role.png`, `02-lambda-config.png`,
  `03-test-invocation.png`, `04-cloudwatch-logs.png`, `05-final-result.png`

## 6. Challenges Faced
- Initial test used naive datetime comparison
  which threw a TypeError since S3's LastModified is timezone-aware — fixed
  by using `datetime.now(timezone.utc)`."]

## 7. Cleanup Performed
- Deleted all test objects used to validate the 2-minute threshold
- Confirmed no other resources (EC2, snapshots, Elastic IPs) were created for
  this task
