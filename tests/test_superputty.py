import unittest

import aws_ssh_config
import io
from contextlib import redirect_stdout




class TestPrintSuperPutty(unittest.TestCase):
    def setUp(self):
        pass


    def tearDown(self) -> None:
        pass

    #########################################################################

    # Happy Journey
    def test_happy_path(self):
        expected = '''<SessionData SessionId="gn1-valnilla1" SessionName="gn1-valnilla1" ImageKey="computer" Host="192.168.0.1" Port="22"
                 Proto="SSH" PuttySession="Default Settings" Username="gregn" ExtraArgs="" SPSLFileName="" RemotePath=""
                 LocalPath=""/>'''
        out = io.StringIO()
        with redirect_stdout(out):
            aws_ssh_config.print_superputty(instance_id='test_instance_id',
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
