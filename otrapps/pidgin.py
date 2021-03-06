#!/usr/bin/env python2.6
# -*- coding: utf-8 -*-

import os
import platform
import sys
import plistlib
import util
from BeautifulSoup import BeautifulSoup

from otr_private_key import OtrPrivateKeys
from otr_fingerprints import OtrFingerprints

class PidginProperties():

    if platform.system() == 'Windows':
        path = os.path.expanduser('~/Application Data/.purple')
    else:
        path = os.path.expanduser('~/.purple')
    accountsfile = 'accounts.xml'
    keyfile = 'otr.private_key'
    fingerprintfile = 'otr.fingerprints'

    @staticmethod
    def _get_resources(settingsdir):
        '''parse out the XMPP Resource from every Pidgin account'''
        resources = dict()
        accountsfile = os.path.join(settingsdir, PidginProperties.accountsfile)
        if not os.path.exists(accountsfile):
            print('Pidgin WARNING: No usable accounts.xml file found, add XMPP Resource to otr.private_key by hand!')
            return resources
        xml = ''
        for line in open(accountsfile, 'r').readlines():
            xml += line
        for e in BeautifulSoup(xml)(text='prpl-jabber'):
            pidginname = e.parent.parent.find('name').contents[0].split('/')
            name = pidginname[0]
            if len(pidginname) == 2:
                resources[name] = pidginname[1]
            else:
                # Pidgin requires an XMPP Resource, even if its blank
                resources[name] = ''
        return resources

    @staticmethod
    def parse(settingsdir=None):
        if settingsdir == None:
            settingsdir = PidginProperties.path

        kf = os.path.join(settingsdir, PidginProperties.keyfile)
        if os.path.exists(kf):
            keydict = OtrPrivateKeys.parse(kf)
        else:
            keydict = dict()

        fpf = os.path.join(settingsdir, PidginProperties.fingerprintfile)
        if os.path.exists(fpf):
            util.merge_keydicts(keydict, OtrFingerprints.parse(fpf))

        resources = PidginProperties._get_resources(settingsdir)
        for name, key in keydict.iteritems():
            if key['protocol'] == 'prpl-jabber' \
                    and 'x' in key.keys() \
                    and name in resources.keys():
                key['resource'] = resources[name]

        return keydict

    @staticmethod
    def write(keydict, savedir):
        if not os.path.exists(savedir):
            raise Exception('"' + savedir + '" does not exist!')

        kf = os.path.join(savedir, PidginProperties.keyfile)
        # Pidgin requires the XMPP resource in the account name field of the
        # OTR private keys file, so fetch it from the existing account info
        if os.path.exists(os.path.join(savedir, PidginProperties.accountsfile)):
            accountsdir = savedir
        elif os.path.exists(os.path.join(PidginProperties.path,
                                         PidginProperties.accountsfile)):
            accountsdir = PidginProperties.path
        resources = PidginProperties._get_resources(accountsdir)

        pidginkeydict = dict()
        for name, key in keydict.iteritems():
            # pidgin requires the XMPP Resource in the account name for otr.private_keys
            if key['protocol'] == 'prpl-jabber' and 'x' in key.keys():
                if name in resources.keys():
                    key['name'] = key['name'] + '/' + resources[name]
                else:
                    key['name'] = key['name'] + '/' + 'REPLACEME'
            pidginkeydict[name] = key
        OtrPrivateKeys.write(pidginkeydict, kf)

        accounts = []
        # look for all private keys and use them for the accounts list
        for name, key in keydict.iteritems():
            if 'x' in key:
                accounts.append(name)
        fpf = os.path.join(savedir, PidginProperties.fingerprintfile)
        OtrFingerprints.write(keydict, fpf, accounts)


if __name__ == '__main__':

    import pprint

    print 'Pidgin stores its files in ' + PidginProperties.path

    if len(sys.argv) == 2:
        settingsdir = sys.argv[1]
    else:
        settingsdir = '../tests/pidgin'

    keydict = PidginProperties.parse(settingsdir)
    pprint.pprint(keydict)

    PidginProperties.write(keydict, '/tmp')
