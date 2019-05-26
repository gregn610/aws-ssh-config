#!/usr/bin/env python

import argparse
import re
import sys
import time
import boto3

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


def handle_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--default-user',
        help='Default ssh username to use'
             'if it can\'t be detected from AMI name')
    parser.add_argument(
        '--keydir',
        default='~/.ssh/',
        help='Location of private keys')
    parser.add_argument(
        '--no-identities-only',
        action='store_true',
        help='Do not include IdentitiesOnly=yes in ssh config; may cause'
             ' connection refused if using ssh-agent')
    parser.add_argument(
        '--postfix',
        default='',
        help='Specify a postfix to append to all host names')
    parser.add_argument(
        '--prefix',
        default='',
        help='Specify a prefix to prepend to all host names')
    parser.add_argument(
        '--private',
        action='store_true',
        help='Use private IP addresses (public are used by default)')
    parser.add_argument(
        '--profile',
        help='Specify AWS credential profile to use')
    parser.add_argument(
        '--proxy',
        default='',
        help='Specify a bastion host for ProxyCommand')
    parser.add_argument(
        '--region',
        action='store_true',
        help='Append the region name at the end of the concatenation')
    parser.add_argument(
        '--ssh-key-name',
        default='',
        help='Override the ssh key to use')
    parser.add_argument(
        '--strict-hostkey-checking',
        action='store_true',
        help='Do not include StrictHostKeyChecking=no in ssh config')
    parser.add_argument(
        '--tags',
        help='A comma-separated list of tag names to be considered for'
             ' concatenation. If omitted, all tags will be used')
    parser.add_argument(
        '--user',
        help='Override the ssh username for all hosts')
    parser.add_argument(
        '--white-list-region',
        default='',
        help='Which regions must be included. If omitted, all regions'
             ' are considered',
        nargs='+')
    args = parser.parse_args()
    return args


def generate_id(instance, tags_filter, region):
    instance_id = ''

    if tags_filter is not None:
        for t_filter in tags_filter.split(','):
            for aws_tag in instance.get('Tags', []):  # ToDo: Swap loop order to make less calls
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

    if region:
        instance_id += '-' + instance[
            'Instances'][0]['Placement']['AvailabilityZone']

    return instance_id


def print_config(ami_image_id, host_id, instance_id, image_id, keyname,
                 ip_addr, keydir, ssh_key_name, no_identities_only, strict_hostkey_checking, proxy):
    if instance_id:
        print('# id: ' + instance_id)
    print('Host ' + host_id)
    print('    HostName ' + ip_addr)
    if ami_image_id is not None:
        print('    User ' + ami_image_id)
    if keydir:
        key_dir = keydir
    else:
        key_dir = '~/.ssh/'
    if ssh_key_name:
        print('    IdentityFile '
              + key_dir + ssh_key_name + '.pem')
    else:
        key_name = AMI_IDS_TO_KEY.get(
            image_id,
            keyname)

        print('    IdentityFile '
              + key_dir + key_name.replace(' ', '_') + '.pem')
    if not no_identities_only:
        # ensure ssh-agent keys don't flood
        # when we know the right file to use
        print('    IdentitiesOnly yes')
    if not strict_hostkey_checking:
        print('    StrictHostKeyChecking no')
    if proxy:
        print('    ProxyCommand ssh ' + proxy + ' -W %h:%p')
    print('')


def process_aws(args_profile,
                args_tags_filter,
                args_region,
                args_white_list_region,
                args_user,
                args_default_user,
                args_private,
                args_prefix,
                args_postfix):
    """
    :return: a list of (ami_image_id, host_id, instance_id, image_id, key_name, ip_addr) tuples
    """
    ret = []
    instances = {}  # dict keyed on InstanceId, value is the instance
    counts_total = {}
    counts_incremental = {}
    amis = AMI_IDS_TO_USER.copy()  # ToDo: Global

    if args_profile:
        session = boto3.Session(profile_name=args_profile)
        regions = session.client('ec2').describe_regions()['Regions']
    else:
        regions = boto3.client('ec2').describe_regions()['Regions']

    for region in regions:
        if (args_white_list_region
                and region['RegionName'] not in args_white_list_region):
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

                host_id = generate_id(instance, args_tags_filter, args_region)

                if host_id not in counts_total:
                    counts_total[host_id] = 0
                    counts_incremental[host_id] = 0

                counts_total[host_id] += 1

                if args_user:
                    amis[instance['ImageId']] = args_user
                else:
                    if not instance['ImageId'] in amis:
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
                                amis[instance['ImageId']] = user
                                break

                        if instance['ImageId'] not in amis:

                            amis[
                                instance['ImageId']
                            ] = args_default_user
                            if args_default_user is None:
                                image_label = image[
                                    'Images'
                                ][0][
                                    'ImageId'] if len(image['Images']) and image['Images'][0] is not None else launch_request[
                                    'Instances'][0]['ImageId']
                                sys.stderr.write(
                                    'Can\'t lookup user for AMI \'' + image_label + '\', add a rule to the script\n')

    for k, instance in instances.items():
        if args_private:
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

        if counts_total[host_id] != 1:
            counts_incremental[host_id] += 1
            host_id += '-' + str(counts_incremental[host_id])

        ssh_config_id = args_prefix + host_id + args_postfix
        ssh_config_id = ssh_config_id.replace(' ', '_').lower()  # get rid of spaces

        ret.append(
            (amis[instance['ImageId']],
             ssh_config_id,
             instance['InstanceId'],
             instance['ImageId'],
             instance['KeyName'],
             ip_addr,
             )
        )
    return ret


def main():
    args = handle_args()

    print('# Generated on ' + time.asctime(time.localtime(time.time())))
    print('# ' + ' '.join(sys.argv))
    print('# ')
    print('')

    config_list = process_aws(
        args.profile,
        args.tags,
        args.region,
        args.white_list_region,
        args.user,
        args.default_user,
        args.private,
        args.prefix,
        args.postfix, )

    for (ami_image_id, host_id, instance_id, image_id, key_name, ip_addr) in config_list:
        print_config(ami_image_id, host_id, instance_id, image_id, key_name, ip_addr,
                     args.keydir,
                     args.ssh_key_name,
                     args.no_identities_only,
                     args.strict_hostkey_checking,
                     args.proxy)


if __name__ == '__main__':
    main()
