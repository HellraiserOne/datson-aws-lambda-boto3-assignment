Task: AWS Daily Cost Alert
1. Objective
Automatically fetch the previous day's AWS cost and usage metrics and deliver a formatted summary alert via SNS using AWS Lambda, triggered by a daily EventBridge schedule — for proactive cost tracking and budget management.

2. Architecture
Lambda Function: aws-daily-cost-alert (Python 3.x, Boto3)
IAM Role: lambda-cost-alert-role — least-privilege inline polic
Trigger: EventBridge rule daily-cost-alert-rule, running on a scheduled cron expression (e.g., 8:00 AM UTC)
Flow: EventBridge cron schedule triggers → invokes Lambda → Lambda queries AWS Cost Explorer API (ce:GetCostAndUsage) for yesterday's spend → Lambda formats message → publishes to SNS Topic → SNS delivers Email/SMS → logs result to CloudWatch

3. IAM Policy
Inline policy attached to lambda-cost-alert-role:
ce:GetCostAndUsage — required to query the Cost Explorer API (cannot be resource-scoped)
sns:Publish — scoped specifically to the destination SNS Topic ARN
AWS managed policy AWSLambdaBasicExecutionRole attached separately to grant CloudWatch Logs write permissions (logs:CreateLogGroup, logs:CreateLogStream, logs:PutLogEvents)
See iam_policy.json for the custom inline policy.

4. Steps Followed
Created an SNS Topic (DailyCostAlerts) and subscribed an email address (and confirmed the subscription)
Created an IAM role with a least-privilege inline policy for Cost Explorer and SNS access
Developed the Lambda function locally utilizing a Python venv virtual environment to test the Boto3 logic securely, then deployed it with the IAM role attached
Wrote Boto3 code to dynamically calculate yesterday's date, query GetCostAndUsage, and format the output into a readable string
Created an EventBridge rule using a schedule expression cron(0 8 * * ? *) to run daily
Set the Lambda function as the rule's target and invoked it manually to test the end-to-end flow
See eventbridge.json for the exact cron schedule used.

5. Testing & Results
Triggered a manual Lambda test event and confirmed it executed successfully
Verified via the Lambda Monitor tab that the function was invoked (1 invocation, 0 errors, 100% success rate)
Confirmed an email was successfully received from SNS containing the formatted AWS cost summary for the previous day
Confirmed CloudWatch Logs showed "Querying Cost Explorer..." and "Successfully published to SNS..." output

Screenshots:
01-sns-topic-subscription.png — SNS topic and confirmed email endpoint
02-iam-role.png — IAM role and inline policy
03-lambda-function.png — Lambda configuration and environment variables
04-event-bridge-cron.png — EventBridge scheduled rule
05-email-alert-result.png — The actual cost alert email received
06-cloudwatch-logs.png — CloudWatch log execution output

6. Challenges Faced
Initially, the Boto3 ce:GetCostAndUsage call failed with a validation error because the TimePeriod parameters must be strictly formatted as YYYY-MM-DD strings, and the start/end dates must span exactly one day for daily granularity. Fixed the Python datetime formatting logic to accurately pass yesterday's date as Start and today's date as End.
The SNS publish step succeeded in Lambda, but no email was received. Root cause: the SNS email subscription was still in a "PendingConfirmation" state. Had to manually log into the destination email account and click the AWS confirmation link before alerts would deliver.
Encountered a slight delay in cost metric accuracy. Learned that AWS Cost Explorer data can have a billing pipeline delay of up to 24 hours. Running the alert too early in the day (e.g., 12:01 AM) occasionally returned incomplete data for the previous day. Adjusted the EventBridge cron schedule to run later in the morning to ensure the metrics were fully finalized.

8. Cleanup Performed
Disabled the EventBridge rule after testing to prevent ongoing daily emails while finalizing the codebase
Deleted the test SNS email subscription to ensure only production endpoints remain active once fully deployed
