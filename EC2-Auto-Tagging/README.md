# Task 3: Auto-Tagging EC2 Instances on Launch

## 1. Objective
Automatically tag newly launched EC2 instances with a launch date and
environment label using AWS Lambda, triggered by EventBridge whenever an
instance transitions to the "running" state — for resource tracking,
ownership, and cost allocation.

## 2. Architecture
- **Lambda Function**: `ec2-auto-tagging` (Python 3.12, Boto3)
- **IAM Role**: `lambda-ec2-autotag-role` — least-privilege inline policy
- **Trigger**: EventBridge rule `ec2-running-autotag-rule`, matching EC2
  "running" state-change events

Flow: EC2 instance state changes to "running" → EventBridge rule matches
event pattern → invokes Lambda → Lambda reads instance ID from event →
tags instance → logs result to CloudWatch

## 3. IAM Policy
Inline policy attached to `lambda-ec2-autotag-role`:
- `ec2:CreateTags` — scoped to instance resources
- `ec2:DescribeInstances` — cannot be resource-scoped by AWS
- AWS managed policy `AWSLambdaBasicExecutionRole` attached separately to
  grant CloudWatch Logs write permissions (`logs:CreateLogGroup`,
  `logs:CreateLogStream`, `logs:PutLogEvents`)

See [`iam_policy.json`](./iam_policy.json) for the custom inline policy.

## 4. Steps Followed
1. Created IAM role with least-privilege inline policy for EC2 tagging
2. Created Lambda function (Python 3.12) with the IAM role attached
3. Wrote Boto3 code to extract `detail.instance-id` from the incoming
   EventBridge event and apply `LaunchDate` and `Environment` tags
4. Created an EventBridge rule matching `source: aws.ec2`,
   `detail-type: EC2 Instance State-change Notification`, `state: running`
5. Set the Lambda function as the rule's target
6. Launched a t3.micro test instance to trigger the flow end-to-end

See [`eventbridge.json`](./eventbridge.json) for the exact event pattern used.

## 5. Testing & Results
- Launched a test EC2 instance and confirmed it reached "running"
- Verified via Lambda's Monitor tab that the function was invoked
  successfully (3 invocations, 0 errors, 100% success rate)
- Confirmed `LaunchDate` and `Environment` tags appeared on the instance
- Confirmed CloudWatch Logs showed "Processing instance..." and
  "Tagged instance..." output
- Screenshots:
  - `01-iam-role.png` — IAM role and inline policy
  - `02-lambda-function.png` — Lambda configuration
  - `03-event-bridge.png`, `03-event-bridge2.png` — EventBridge rule and
    event pattern
  - `04-final-result-tags.png` — tags applied on the EC2 instance
  - `05-cloudwatch-logs.png` — CloudWatch log output

## 6. Challenges Faced
- Initial invocations were silently failing to produce any CloudWatch logs,
  which looked like the Lambda was never being triggered. EventBridge
  metrics (TriggeredRules, InvocationAttempts) showed activity, and Lambda's
  own Invocations/Errors graph confirmed 3 successful invocations with 0
  errors — but no log group existed. Root cause: the Lambda execution role
  only had the custom EC2 inline policy and was missing the basic
  `logs:CreateLogGroup` / `logs:CreateLogStream` / `logs:PutLogEvents`
  permissions. Fixed by attaching the AWS managed policy
  `AWSLambdaBasicExecutionRole` to the role.
- Also had to manually add a resource-based policy statement (Principal:
  `events.amazonaws.com`, Action: `lambda:InvokeFunction`) to the Lambda
  function, since it wasn't auto-created when the EventBridge target was
  first added.
- The EventBridge rule only fires on a genuine transition to "running" —
  an instance already running before the rule existed doesn't trigger it.
  Had to stop and restart the test instance to generate a fresh event.

## 7. Cleanup Performed
- Terminated the test EC2 instance immediately after confirming tags and
  logs
- Confirmed no other lingering resources (Elastic IPs, extra instances)
