import boto3
import os
from datetime import datetime, timedelta

ce = boto3.client('ce')
sns = boto3.client('sns')

SNS_TOPIC_ARN = os.environ.get('SNS_TOPIC_ARN', 'arn:aws:sns:us-east-1:626159998134:cost-alert-topic')
THRESHOLD = float(os.environ.get('THRESHOLD', '50'))

def lambda_handler(event, context):
    today = datetime.utcnow().date()
    start_of_month = today.replace(day=1)

    response = ce.get_cost_and_usage(
        TimePeriod={
            'Start': start_of_month.strftime('%Y-%m-%d'),
            'End': today.strftime('%Y-%m-%d')
        },
        Granularity='MONTHLY',
        Metrics=['UnblendedCost']
    )

    amount = float(response['ResultsByTime'][0]['Total']['UnblendedCost']['Amount'])
    unit = response['ResultsByTime'][0]['Total']['UnblendedCost']['Unit']

    print(f"Month-to-date cost: {amount:.4f} {unit}")
    print(f"Threshold: {THRESHOLD} {unit}")

    if amount > THRESHOLD:
        message = (
            f"AWS Cost Alert: Month-to-date spend is {amount:.2f} {unit}, "
            f"which exceeds your threshold of {THRESHOLD} {unit}."
        )
        sns.publish(
            TopicArn=SNS_TOPIC_ARN,
            Subject="AWS Cost Alert",
            Message=message
        )
        print("Alert published to SNS.")
    else:
        print("Spend is within threshold. No alert sent.")

    return {
        'statusCode': 200,
        'amount': amount,
        'threshold': THRESHOLD,
        'alert_sent': amount > THRESHOLD
    }