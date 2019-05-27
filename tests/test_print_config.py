import unittest

import aws_ssh_config
import io
from contextlib import redirect_stdout




class TestPrintConfig(unittest.TestCase):
    def setUp(self):
        pass


    def tearDown(self) -> None:
        pass

    #########################################################################

    # Happy Journey
    def test_happy_path(self):
        expected = '''# id: test_instance_id
Host test_host_id
    HostName test_ip_addr
    User test_host_user
    IdentityFile test_key_dir\\test_ssh_key_name.pem
    ProxyCommand ssh test_proxy -W %h:%p

'''
        out = io.StringIO()
        with redirect_stdout(out):
            aws_ssh_config.print_config(instance_id='test_instance_id',
                                        host_id='test_host_id',
                                        ip_addr='test_ip_addr',
                                        host_user='test_host_user',
                                        key_dir='test_key_dir',
                                        ssh_key_name='test_ssh_key_name',
                                        launch_key_name='test_launch_key_name',
                                        no_identities_only='test_no_identities_only',
                                        strict_hostkey_checking='test_strict_hostkey_checking',
                                        proxy='test_proxy')
        actual = out.getvalue()
        self.assertEqual(expected, actual)


    def test_barebones1(self):
        expected = '''Host test_host_id
    HostName test_ip_addr
    IdentityFile test_key_dir\\test_ssh_key_name.pem
    StrictHostKeyChecking no

'''
        out = io.StringIO()
        with redirect_stdout(out):
            aws_ssh_config.print_config(instance_id=None,
                                        host_id='test_host_id',
                                        ip_addr='test_ip_addr',
                                        host_user=None,
                                        key_dir='test_key_dir',
                                        ssh_key_name='test_ssh_key_name',
                                        launch_key_name=None,
                                        no_identities_only=True,
                                        strict_hostkey_checking=False,
                                        proxy=None)

        actual = out.getvalue()
        self.assertEqual(expected, actual)

