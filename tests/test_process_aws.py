import unittest
import aws_ssh_config


class TestProcessAWS(unittest.TestCase):
    def setUp(self):
        self.empty_args = {
            'args_profile': '',
            'args_tags_filter': None,
            'args_region_suffix': False,
            'args_whitelist_regions': '',
            'args_user': '',
            'args_default_user': '',
            'args_private_ip': False,
            'args_host_prefix': '',
            'args_host_postfix': ''
        }

    def tearDown(self) -> None:
        pass

#########################################################################
# ToDo: Sort out mocking out AWS
    # Happy Journey
    def test_happy_path(self):
        # list[tuple(
        #     ssh_config_id,
        #     instance['ImageId'],
        #     instance['InstanceId'],
        #     instance['ImageId'],
        #     launch_key_name,
        #     ip_addr
        # ), ]
        pass
        #expected = [
        #        ('centos7-demo-2.2.0',
        #            '', 'i-0000ce0e00000000f', 'ami-0b0c00a0fe00aeb00', 'demo-new', '111.111.111.111')]
        #actual = aws_ssh_config.process_aws(**self.empty_args)
        #self.assertEqual(expected, actual)
