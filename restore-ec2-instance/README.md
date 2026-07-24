# Task 5: Restore an EC2 Instance from the Latest Snapshot

## 1. Objective
Automate disaster recovery by restoring an EC2 instance's root volume from
its most recent EBS snapshot, using AWS Lambda and Boto3.

## 2. Architecture
- **Lambda Function**: `ec2-snapshot-restor` (Python 3.12, Boto3)
- **IAM Role**: least-privilege inline policy for snapshot lookup and
  volume/instance operations
- **Target Instance**: `i-0f0794dced05c40b4` (root volume:
  `vol-046f7ce243eee14bc`)
- **Trigger**: Manual invocation

Flow: Manual Invoke → Lambda → Finds latest snapshot for the target volume
(sorted by StartTime) → Initiates a root volume replacement from that
snapshot → Logs progress and task ID to CloudWatch

## 3. IAM Policy
Inline policy granting the permissions needed to describe snapshots and
perform the volume replacement:
- `ec2:DescribeSnapshots`
- `ec2:DescribeInstances`
- `ec2:CreateReplaceRootVolumeTask` (or `ec2:RegisterImage` /
  `ec2:RunInstances`, depending on approach)
- `ec2:CreateTags`
- AWS managed policy `AWSLambdaBasicExecutionRole` for CloudWatch Logs

See [`iam_policy.json`](./iam_policy.json) for the exact policy used.

## 4. Approach Note
The assignment's reference approach was to register a new AMI from the
snapshot (`RegisterImage`) and launch a brand-new instance from it
(`RunInstances`). This implementation instead uses EC2's
**CreateReplaceRootVolumeTask** — which restores the *existing* instance's
root volume in-place from a snapshot rather than creating a new instance.
This achieves the same disaster-recovery objective (restore an instance
to a known-good state from its latest snapshot) with less resource sprawl,
since no new instance/AMI needs to be tracked or cleaned up afterward.

## 5. Steps Followed
1. Created an EBS snapshot of the target instance's root volume
2. Created IAM role with least-privilege inline policy
3. Created Lambda function (Python 3.12) with the IAM role attached
4. Wrote Boto3 code to find the most recent snapshot for the given volume
   (sorted by StartTime) and initiate a root volume replacement task
5. Tested via manual invocation

## 6. Testing & Results
- First test invocation failed with `IncorrectInstanceState`: the target
  EC2 instance was not in the "running" state at the time, and
  `CreateReplaceRootVolumeTask` requires the instance to be running
- Started the instance and re-ran the test
- Second invocation succeeded: response showed
  `"Restoring instance i-0f0794dced05c40b4 using snapshot
  snap-00330d585124d46f0"`, and CloudWatch confirmed
  `Successfully initiated volume replacement. Task ID:
  replacevol-06d3a7f86463673f2`
- Screenshots:
  - `01-ec2-restore-lambda-function.png` — Lambda function code/overview
  - `02-snapshot-created.png` — source snapshot
  - `03-lambda-iam-role.png` — IAM role and policy
  - `04-lambda-invocation.png` — successful test invocation output
  - `04-cloudwatch-logs.png` — CloudWatch logs showing both the failed and
    successful runs
  - `05-lambda-config.png` — Lambda configuration

## 7. Challenges Faced
- First invocation failed with `IncorrectInstanceState` because
  `CreateReplaceRootVolumeTask` requires the target instance to be in the
  "running" state; the instance had been stopped after earlier testing.
  Fixed by starting the instance before retrying.
- Confirmed via CloudWatch Logs that both the failure and the subsequent
  success were fully visible in logs, which was useful for diagnosing the
  root cause without guesswork.

## 8. Cleanup Performed
- terminated any extra test instances/AMIs
- deleted test snapshots no longer needed
- confirmed the restored instance was stopped/terminated if only used for testing
