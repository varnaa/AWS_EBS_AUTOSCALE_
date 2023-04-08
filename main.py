import boto3
import subprocess

# Set the region
region = 'us-east-2'

# Set the instance ID and private key file
instance_id = 'i-0590afd17f98e4093'
private_key_file = '/Users/varnaa/key3.pem'
user_name = 'ec2-user@ec2-'
service_name = '.compute.amazonaws.com'

# Set the maximum used percentage threshold
max_used_threshold = 75

# Create an EC2 client
ec2 = boto3.client('ec2', region_name=region)

# Get information about the instance
instance = ec2.describe_instances(
    InstanceIds=[instance_id]
)['Reservations'][0]['Instances'][0]


print("Instance: ", instance)

# Get the instance IP address
instance_ip = instance['PublicIpAddress']
instance_ip = instance_ip.replace('.', '-')
print("Instance IP: ", instance_ip)

# Get information about all volumes attached to the instance
volumes = ec2.describe_volumes(
    Filters=[{
        'Name': 'attachment.instance-id',
        'Values': [instance_id]
    }]
)

print("Volumes: ", volumes)

# Check each volume and autoscale if necessary
for volume in volumes['Volumes']:
    # Get the volume ID, size, and device name
    volume_id = volume['VolumeId']
    volume_size = volume['Size']
    device_name = volume['Attachments'][0]['Device']

    print("Volume id: ", volume_id)
    print("Total Volume Size: ",volume_size)

    # Run the df command on the remote instance
    result = subprocess.run(
        ['ssh', '-i', private_key_file, f''+user_name+instance_ip+'.'+region+service_name, f'df -h {device_name}'],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )


    # Get the output of the df command
    output = result.stdout.decode('utf-8')
    print("Result from ssh: ", result)


    # Parse the output to get the disk usage information
    lines = output.split('\n')
    print("Lines: ", lines)
    if len(lines) > 1:
        fields = lines[1].split()
        filesystem = fields[0]
        size = fields[1]
        used = fields[2]
        available = fields[3]
        use_percent_str = fields[4]
        mounted_on = fields[5]

        print("Used Percentage: ", use_percent_str)

        # Calculate the used percentage
        use_percent = int(use_percent_str.replace('%', ''))

        # Check if the used percentage is above the maximum used threshold
        if use_percent >= max_used_threshold:
            # Autoscale the volume by increasing its size by 10%
            print("Initiating autoscale")
            #new_size = int(volume_size * 1.1)
            new_size = 9
            print("New Size: ", new_size)
            ec2.modify_volume(
                VolumeId=volume_id,
                Size=new_size
            )
            print(f'Autoscaled volume {volume_id} from {volume_size} GB to {new_size} GB')



