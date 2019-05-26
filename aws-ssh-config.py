#!/usr/bin/env python

"""aws_ssh_config
Generate an SSH config file from AWS instances

Usage:
    aws-ssh-config.py [options]

Options:
  -h, --help                  show this help message and exit
  --default-user DEFAULT_USER Default ssh username to useif it can't be detected from AMI name
  --keydir KEYDIR             Location of private keys
  --no-identities-only        Do not include IdentitiesOnly=yes in ssh config; may cause connection refused if using ssh-agent
  --postfix POSTFIX           Specify a postfix to append to all host names
  --prefix PREFIX             Specify a prefix to prepend to all host names
  --private                   Use private IP addresses (public are used by default)
  --profile PROFILE           Specify AWS credential profile to use
  --proxy PROXY               Specify a bastion host for ProxyCommand
  --region                    Append the region name at the end of the host
  --ssh-key-name SSH_KEY_NAME Override the ssh key to use
  --strict-hostkey-checking   Do not include StrictHostKeyChecking=no in ssh config
  --tags TAGS                 Comma-separated list of tag names to be considered for concatenation. If omitted, all tags will be used
  --user USER                 Override the ssh username for all hosts
  --whitelist-region WHITELIST_REGION[,WHITELIST_REGION ...] Comma separated regions to be included. If omitted, all regions are considered

Examples:
    aws-ssh-config.py --whitelist-region=eu-west-1,eu-west-2

"""
#ToDo: Maybe go with repeatable options rather than once comma separated for tags, whitelist & blacklist

import os
from docopt import docopt
import re
import sys
import time
import boto3
import logging

AMI_NAMES_TO_USER = {
    'amzn': 'ec2-user',
    'ubuntu': 'ubuntu',
    'CentOS': 'root',
    'DataStax': 'ubuntu',
    'CoreOS': 'core'
}

AMI_IDS_TO_USER = {
    'ami-ada2b6c4': 'ubuntu'
}

AMI_IDS_TO_KEY = {
    'ami-ada2b6c4': 'custom_key'
}

BLACKLISTED_REGIONS = [

]



def generate_id(instance, tags_filter, add_region_suffix):
    """
    Use instance details to build the SSH host name
    :param instance:
    :param tags_filter:
    :param add_region_suffix:
    :return:
    """
    instance_id = ''

    if tags_filter is not None:
        for aws_tag in instance.get('Tags', []):
            for t_filter in tags_filter.split(','):
                if aws_tag['Key'] == t_filter:
                    value = aws_tag['Value']
                    if value:
                        if not instance_id:
                            instance_id = value
                        else:
                            instance_id += '-' + value
    else:
        for t_filter in instance.get('Tags', []):
            if not (t_filter['Key']).startswith('aws'):
                if not instance_id:
                    instance_id = t_filter['Value']
                else:
                    instance_id += '-' + t_filter['Value']

    if not instance_id:
        instance_id = instance['InstanceId']

    if add_region_suffix:
        instance_id += '-' + instance['Placement']['AvailabilityZone']

    return instance_id


def print_config(ami_image_id, host_id, instance_id, image_id, keyname,
                 ip_addr, keydir, ssh_key_name, no_identities_only, strict_hostkey_checking, proxy):
    """
    Prints the lines to build an SSH config file
    :return: None
    """

    logging.debug('print_config()')
    if instance_id:
        print('# id: ' + instance_id)
    print('Host ' + host_id)
    print('    HostName ' + ip_addr)
    if ami_image_id is not None:
        print('    User ' + ami_image_id)
    if ssh_key_name:
        print('    IdentityFile ' + os.path.join(keydir, ssh_key_name + '.pem'))
    else:
        key_name = AMI_IDS_TO_KEY.get(
            image_id,
            keyname).replace(' ', '_')

        print('    IdentityFile '
              + os.path.join(keydir, key_name + '.pem'))
    if not no_identities_only:
        # ensure ssh-agent keys don't flood when we know the right file to use
        print('    IdentitiesOnly yes')
    if not strict_hostkey_checking:
        print('    StrictHostKeyChecking no')
    if proxy:
        print('    ProxyCommand ssh ' + proxy + ' -W %h:%p')
    print('')


def process_aws(args_profile,
                args_tags_filter,
                args_region,
                args_whitelist_regions,
                args_user,
                args_default_user,
                args_private_ip,
                args_host_prefix,
                args_host_postfix):
    """
    :return: a list of (ami_image_id, host_id, instance_id, image_id, key_name, ip_addr) tuples
    """
    logging.debug('process_aws()')
    ret = []
    instances = {}  # dict keyed on InstanceId, value is the instance
    counts_total = {}
    counts_incremental = {}
    ami_usernames = AMI_IDS_TO_USER.copy()  # ToDo: Global

    if args_profile:
        session = boto3.Session(profile_name=args_profile)
        regions = session.client('ec2').describe_regions()['Regions']
    else:
        regions = boto3.client('ec2').describe_regions()['Regions']

    for region in regions:
        if (args_whitelist_regions
                and region['RegionName'] not in args_whitelist_regions.split(',')):
            continue
        if region['RegionName'] in BLACKLISTED_REGIONS:
            continue
        if args_profile:
            ec2_service = session.client('ec2', region_name=region['RegionName'], profile_name=args_profile)
        else:
            ec2_service = boto3.client('ec2', region_name=region['RegionName'])

        for launch_request in ec2_service.describe_instances()['Reservations']:
            for instance in launch_request['Instances']:
                if instance['State']['Name'] != 'running':
                    continue

                if instance.get('KeyName', None) is None:
                    continue  # Not interested in instances without SSH keys

                instances[instance['InstanceId']] = instance

                if args_user:
                    ami_usernames[instance['ImageId']] = args_user
                else:
                    if not instance['ImageId'] in ami_usernames:
                        image = ec2_service.describe_images(
                            Filters=[
                                {
                                    'Name': 'image-id',
                                    'Values': [instance['ImageId']]
                                }
                            ]
                        )

                        for ami, user in AMI_NAMES_TO_USER.items():
                            regexp = re.compile(ami)
                            if (len(image['Images']) > 0
                                    and regexp.match(image['Images'][0]['Name'])):
                                ami_usernames[instance['ImageId']] = user
                                break

                        if instance['ImageId'] not in ami_usernames:

                            ami_usernames[
                                instance['ImageId']
                            ] = args_default_user
                            if args_default_user is None:
                                if len(image['Images']) and image['Images'][0] is not None:
                                    image_label = image['Images'][0]['ImageId']
                                else:
                                    image_label = launch_request[instance['ImageId']]
                                logging.warning("Lookup user for AMI '{0}' failed, add a rule to the script".format(image_label))

    for k, instance in instances.items():
        if args_private_ip:
            if instance['PrivateIpAddress']:
                ip_addr = instance['PrivateIpAddress']
        else:
            try:
                ip_addr = instance['PublicIpAddress']
            except KeyError:
                try:
                    ip_addr = instance['PrivateIpAddress']
                except KeyError:
                    sys.stderr.write(
                        'Cannot lookup ip address for instance %s,'
                        ' skipped it.'
                        % instance['InstanceId'])
                    continue

        host_id = generate_id(instance, args_tags_filter, args_region)

        if host_id not in counts_total:
            counts_total[host_id] = 0
            counts_incremental[host_id] = 0

        counts_total[host_id] += 1

        if counts_total[host_id] != 1:
            counts_incremental[host_id] += 1
            host_id += '-' + str(counts_incremental[host_id])

        ssh_config_id = args_host_prefix + host_id + args_host_postfix
        ssh_config_id = ssh_config_id.replace(' ', '_').lower()  # get rid of spaces

        ret.append(
            (ami_usernames[instance['ImageId']],
             ssh_config_id,
             instance['InstanceId'],
             instance['ImageId'],
             instance['KeyName'],
             ip_addr,
             )
        )
    return ret


def main(args):
    logging.debug('main()')
    # neater than docopt [default: ]
    for k in (
            '--default-user', '--user', '--tags', '--prefix', '--postfix', '--keydir', '--proxy',
            '--ssh-key-name', '--profile', '--whitelist-region', ):
        if args[k] is None: args[k] = ''

    print('# Generated on ' + time.asctime(time.localtime(time.time())))
    print('# ' + ' '.join(sys.argv))
    print('# ')
    print('')

    config_list = process_aws(
        args['--profile'],
        args['--tags'],
        args['--region'],
        args['--whitelist-region'],
        args['--user'],
        args['--default-user'],
        args['--private'],
        args['--prefix'],
        args['--postfix'], )

    for (ami_image_id, host_id, instance_id, image_id, key_name, ip_addr) in config_list:
        print_config(ami_image_id, host_id, instance_id, image_id, key_name, ip_addr,
                     args['--keydir'],
                     args['--ssh-key-name'],
                     args['--no-identities-only'],
                     args['--strict-hostkey-checking'],
                     args['--proxy'])


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format='%(message)s')
    arguments = docopt(__doc__, version='aws_ssh_config 0.2')
    logging.debug("Command line arguments: {0}".format(arguments))
    main(arguments)

