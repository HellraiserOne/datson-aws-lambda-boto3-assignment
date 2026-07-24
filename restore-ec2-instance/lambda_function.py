import boto3
import os
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)
ec2 = boto3.client('ec2')

def lambda_handler(event, context):
    instance_id = os.environ['INSTANCE_ID']
    
    try:
        # 1. Identify the root volume
        response = ec2.describe_instances(InstanceIds=[instance_id])
        instance = response['Reservations'][0]['Instances'][0]
        root_device_name = instance['RootDeviceName']
        
        root_volume_id = None
        for mapping in instance.get('BlockDeviceMappings', []):
            if mapping['DeviceName'] == root_device_name:
                root_volume_id = mapping['Ebs']['VolumeId']
                break
                
        if not root_volume_id:
            raise Exception("Root volume not found on instance.")
            
        logger.info(f"Target Instance: {instance_id} | Root Volume: {root_volume_id}")
        
        # 2. Find the most recent snapshot for this volume
        snapshots = ec2.describe_snapshots(
            Filters=[{'Name': 'volume-id', 'Values': [root_volume_id]}],
            OwnerIds=['self']
        )['Snapshots']
        
        if not snapshots:
            raise Exception("No snapshots found for this root volume. Please create one for testing.")
            
        # Sort descending by start time to grab the latest
        latest_snapshot = sorted(snapshots, key=lambda x: x['StartTime'], reverse=True)[0]
        snapshot_id = latest_snapshot['SnapshotId']
        logger.info(f"Latest Snapshot Found: {snapshot_id}")
        
        # 3. Trigger the root volume replacement task
        replace_task = ec2.create_replace_root_volume_task(
            InstanceId=instance_id,
            SnapshotId=snapshot_id
        )
        
        task_id = replace_task['ReplaceRootVolumeTaskId']
        logger.info(f"Successfully initiated volume replacement. Task ID: {task_id}")
        
        return {
            'statusCode': 200,
            'body': f"Restoring instance {instance_id} using snapshot {snapshot_id}"
        }
        
    except Exception as e:
        logger.error(f"Error during restoration: {str(e)}")
        raise e