import unittest
import datetime
from dateutil.tz import tzutc

import aws_ssh_config

class TestGenerateId(unittest.TestCase):
    def setUp(self):
        self.basic_instance = {'AmiLaunchIndex': 0, 
                               'ImageId': 'ami-0b0c00a0fe00aeb00',
                               'InstanceId': 'i-0000ce0e00000000f', 
                               'InstanceType': 'r4.4xlarge',
                               'KeyName': 'demo-new',
                               'LaunchTime': datetime.datetime(2019, 3, 28, 14, 7, 26, tzinfo=tzutc()),
                               'Monitoring': {'State': 'disabled'},
                               'Placement': {'AvailabilityZone': 'eu-west-1a', 'GroupName': '', 'Tenancy': 'default'},
                               'PrivateDnsName': 'ip-10-128-8-88.eu-west-1.compute.internal',
                               'PrivateIpAddress': '10.128.8.88', 
                               'ProductCodes': [{'ProductCodeId': 'aw0evgkw8e5c1q413zgy5pjce', 'ProductCodeType': 'marketplace'}],
                               'PublicDnsName': 'ec2-111.111.111.111.eu-west-1.compute.amazonaws.com',
                               'PublicIpAddress': '111.111.111.111', 
                               'State': {'Code': 16, 'Name': 'running'},
                               'StateTransitionReason': '', 
                               'SubnetId': 'subnet-00a00000de000000d',
                               'VpcId': 'vpc-0d0000000a00e0a0e', 
                               'Architecture': 'x86_64', 
                               'BlockDeviceMappings': [
                                    {'DeviceName': '/dev/sda1',
                                    'Ebs': {'AttachTime': datetime.datetime(2019, 3, 28, 14, 7, 26, tzinfo=tzutc()),
                                            'DeleteOnTermination': True, 'Status': 'attached', 'VolumeId': 'vol-0e0c00d0c0d0cedd0'}
                                    },
                                    {'DeviceName': '/dev/sdb',
                                    'Ebs': {'AttachTime': datetime.datetime(2019, 3, 28, 14, 7, 26, tzinfo=tzutc()),
                                            'DeleteOnTermination': True, 'Status': 'attached', 'VolumeId': 'vol-0000f0a0a0000ce00'}}
                               ],
                               'ClientToken': '', 
                               'EbsOptimized': True, 
                               'EnaSupport': True, 
                               'Hypervisor': 'xen',
                               'IamInstanceProfile': {}, 
                               'NetworkInterfaces': [],
                               'RootDeviceName': '/dev/sda1', 'RootDeviceType': 'ebs',
                               'SecurityGroups': [{'GroupName': 'demo-dev-access', 'GroupId': 'sg-0fbad0000b0bc0000'},
                                                  {'GroupName': 'demo-new-subnet', 'GroupId': 'sg-000000cb00c0fc00e'},
                                                  {'GroupName': 'demo-new-egress', 'GroupId': 'sg-000e000000000ce0f'},
                                                  ],
                               'SourceDestCheck': True,
                               'Tags': [
                                    {'Key': 'Name', 'Value': 'testapp'},
                                    {'Key': 'Terraform', 'Value': 'True'},
                                    {'Key': 'Environment', 'Value': 'dev'},
                                    {'Key': 'RPZ', 'Value': 'True'},
                                    {'Key': 'Application', 'Value': 'turing'},
                                    {'Key': 'Warehouse', 'Value': 'True'},
                                    {'Key': 'Build', 'Value': '-1'},
                                    {'Key': 'Feeds', 'Value': 'True'},
                                    {'Key': 'Platform', 'Value': 'centos7'},
                                    {'Key': 'Product', 'Value': 'acmeapp'},
                                    {'Key': 'Version', 'Value': '2.2.0'}
                                ],
                               'VirtualizationType': 'hvm',
                               'CpuOptions': {'CoreCount': 8, 'ThreadsPerCore': 2},
                               'CapacityReservationSpecification': {'CapacityReservationPreference': 'open'},
                               'HibernationOptions': {'Configured': False}
                               }
        self.no_tags = self.basic_instance.copy()
        self.no_tags['Tags'] = []

    def tearDown(self) -> None:
        pass

    #########################################################################

    # Happy Journey
    def test_happy_path(self):
        expected = 'testapp-centos7-acmeapp-eu-west-1a'
        actual = aws_ssh_config.generate_id(self.basic_instance, 'Platform,Name,Product', True)
        self.assertEqual(expected, actual)

    def test_no_region_suffix(self):
        expected = 'testapp-centos7-acmeapp'
        actual = aws_ssh_config.generate_id(self.basic_instance, 'Platform,Name,Product', False)
        self.assertEqual(expected, actual)

    def test_instance_no_tags(self):
        expected = 'i-0000ce0e00000000f-eu-west-1a'
        actual = aws_ssh_config.generate_id(self.no_tags, 'Platform,Name,Product', True)
        self.assertEqual(expected, actual)

    def test_no_tags_filter(self):
        expected = 'i-0000ce0e00000000f-eu-west-1a'
        actual = aws_ssh_config.generate_id(self.no_tags, None, True)
        self.assertEqual(expected, actual)

    def test_no_tags_filter2(self):
        expected = 'i-0000ce0e00000000f-eu-west-1a'
        actual = aws_ssh_config.generate_id(self.no_tags, '', True)
        self.assertEqual(expected, actual)
