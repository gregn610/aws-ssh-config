import unittest
from docopt import docopt

import io
import subprocess
from contextlib import redirect_stdout, redirect_stderr

class TestCommandLine(unittest.TestCase):
    def setUp(self):
        import aws_ssh_config as asc
        self.doc_string = asc.__doc__


    def tearDown(self) -> None:
        pass

    #########################################################################

    # Happy Journey
    def test_happy_path(self):
        test_sysv = [
            '--default-user', 'test_user',
            '--key-dir', 'test_key_dir',
            '--no-identities-only',
            '--postfix', 'test_postfix',
            '--prefix', 'test_prefix',
            '--private',
            '--profile', 'test_profile',
            '--proxy', 'test_proxy',
            '--region-suffix',
            '--ssh-key-name', 'test_ssh_key_name',
            '--strict-hostkey-checking',
            '--tags', 'test_tag1,test_tag21,test_tag3',
            '--user', 'test_user',
            '--whitelist-region', 'test_wl_region1,test_wl_region2,test_wl_region3' ]

        expected = {'--default-user': 'test_user',
                     '--help': False,
                     '--key-dir': 'test_key_dir',
                     '--no-identities-only': True,
                     '--postfix': 'test_postfix',
                     '--prefix': 'test_prefix',
                     '--private': True,
                     '--profile': 'test_profile',
                     '--proxy': 'test_proxy',
                     '--region-suffix': True,
                     '--ssh-key-name': 'test_ssh_key_name',
                     '--strict-hostkey-checking': True,
                     '--tags': 'test_tag1,test_tag21,test_tag3',
                     '--user': 'test_user',
                     '--whitelist-region': 'test_wl_region1,test_wl_region2,test_wl_region3'}
        actual = docopt(self.doc_string, test_sysv)
        self.assertEqual(expected, actual)

    def test_no_args(self):
        test_sysv = []

        expected = { '--default-user': None,
                     '--help': False,
                     '--key-dir': None,
                     '--no-identities-only': False,
                     '--postfix': None,
                     '--prefix': None,
                     '--private': False,
                     '--profile': None,
                     '--proxy': None,
                     '--region-suffix': False,
                     '--ssh-key-name': None,
                     '--strict-hostkey-checking': False,
                     '--tags': None,
                     '--user': None,
                     '--whitelist-region': None}
        actual = docopt(self.doc_string, test_sysv)
        self.assertEqual(expected, actual)

# ToDo: where is subprocess output going?
#    def test_help(self):
#        '''
#        Check basic -h --help works. Because docopt exitson -h, test with subprocess
#        '''
#        actual = None
#        try:
#            actual = subprocess.check_output(['aws_ssh_config.py', '-h'], shell=True, stderr=subprocess.STDOUT,).decode('ascii').rstrip()
#        except subprocess.CalledProcessError as e:
#            self.assertEqual(1, e.returncode)
#            actual = e.stdout.decode('ascii').rstrip().replace('\r\n', '\n')
#
#        # Just loosely matches regexes. Don't need to update/fail test for every minor edit
#        self.assertIn('Usage:', actual)
#        self.assertIn('Options:', actual)
#        self.assertRegex(actual, r'\s+--default-user DEFAULT_USER')
#        self.assertRegex(actual, r'\s+--key-dir KEY_DIR')
#        self.assertRegex(actual, r'\s+--no-identities-only')
#        self.assertRegex(actual, r'\s+--prefix PREFIX')
#        self.assertRegex(actual, r'\s+--postfix POSTFIX')
#        self.assertRegex(actual, r'\s+--private')
#        self.assertRegex(actual, r'\s+--profile PROFILE')
#        self.assertRegex(actual, r'\s+--proxy PROXY')
#        self.assertRegex(actual, r'\s+--region-suffix')
#        self.assertRegex(actual, r'\s+--ssh-key-name SSH_KEY_NAME')
#        self.assertRegex(actual, r'\s+--strict-hostkey-checking')
#        self.assertRegex(actual, r'\s+--tags TAGS')
#        self.assertRegex(actual, r'\s+--user USER')



