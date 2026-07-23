# Task 2: Automated EBS Snapshot Creation and Cleanup

## 1. Objective
Automate EBS volume backups using AWS Lambda and Boto3 — creating a tagged
snapshot on each run and deleting snapshots older than a defined retention
period (30 days in production).

## 2. Architecture
- **EBS Volume**: `vol-05666e2b54e1a9538` (us-east-1)
- **Lambda Function**: `datson-ebs-snapshot-cleanup` (Python 3.12, Boto3)
- **IAM Role**: `lambda-ebs-snapshot-role` — least-privilege inline policy
- **Trigger**: EventBridge scheduled rule (weekly) + manual invocation for testing

Flow: EventBridge (weekly) / Manual Invoke → Lambda → Creates + tags snapshot
→ Lists tagged snapshots owned by account → Deletes those past retention →
Logs results to CloudWatch

## 3. IAM Policy
Inline policy attached to `lambda-ebs-snapshot-role`:
- `ec2:CreateSnapshot` — scoped to the specific volume and to snapshot resources
- `ec2:CreateTags` — scoped to snapshot resources
- `ec2:DescribeSnapshots`, `ec2:DeleteSnapshot` — cannot be resource-scoped by
  AWS, so restricted in code instead: only snapshots tagged
  `CreatedBy=Lambda-Backup` and owned by this account are ever touched

See [`iam_policy.json`](./iam_policy.json) for the exact policy used.

## 4. Steps Followed
1. Created a 1 GiB gp3 EBS volume in us-east-1
2. Created IAM role with least-privilege inline policy
3. Created Lambda function (Python 3.12) with the IAM role attached
4. Wrote Boto3 code to create + tag a snapshot, then list and delete snapshots
   past the retention threshold
5. Used environment variables (`VOLUME_ID`, `RETENTION_DAYS`) to control
   behavior without editing code
6. Deployed and tested with `RETENTION_DAYS=0` to force and verify delete logic
   before resetting to 30 (production value)
7. Created an EventBridge rule to schedule the function weekly

## 5. Testing & Results
- First test run: successfully created and tagged a new snapshot
- Verified snapshot appeared in EC2 → Snapshots with `CreatedBy=Lambda-Backup`
- Set `RETENTION_DAYS=0` and re-ran to confirm delete logic correctly removed
  the snapshot(s)
- Confirmed via EC2 console that snapshots were deleted as expected
- Reset `RETENTION_DAYS=30` for the final/production configuration
- Screenshots:
  - `01-iam-role-lambda.png`, `01-iam-role-lambda2.png` — IAM role & policy
  - `02-lambda-configuration.png` — Lambda config
  - `03-snapshot-cleanup.png`, `03-snapshot-cleanup2.png` — test invocation output
  - `04-cloudwatch-logs.png` — CloudWatch logs
  - `04-snapshot-creation.png` — snapshot visible in EC2 console
  - `05-final-result.png` — final state after cleanup logic ran
  - `06-snapshots-deleted.png` — confirmation snapshots were removed
  - `07-eventbridge-schedule.png`, `07-eventbridge-schedule2.png` — weekly
    EventBridge rule configuration

## 6. Challenges Faced
- Initial test failed with `InvalidVolume.NotFound` — the EBS volume had been
  created in a different region than the Lambda function. Fixed by ensuring
  both the volume and the Lambda function were in us-east-1.
- Second issue: `UnauthorizedOperation` on `ec2:CreateTags` — the inline
  policy's `Condition` block (restricting tagging to `CreateAction:
  CreateSnapshot`) wasn't matching as expected. Fixed by simplifying the
  policy to grant `ec2:CreateTags` on snapshot resources without the
  condition.

## 7. Cleanup Performed
- Deleted test snapshots created during the `RETENTION_DAYS=0` verification run
- Deleted the EBS volume (`vol-05666e2b54e1a9538`) after testing was complete
- [State whether you kept or deleted the EventBridge rule]
- Confirmed no other resources (EC2 instances, Elastic IPs) were left running
