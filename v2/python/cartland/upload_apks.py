#!/usr/bin/python
#
# Copyright 2014 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the 'License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Uploads an apk to the alpha track."""

import argparse
import sys

from apiclient.discovery import build
import httplib2
from oauth2client import client
from oauth2client.service_account import ServiceAccountCredentials

TRACK_OPTIONS = ['alpha', 'beta', 'production', 'rollout']

# <package name> <file.apk> --track alpha

# Declare command-line flags.
argparser = argparse.ArgumentParser(add_help=False)
argparser.add_argument('package_name',
                       help='The package name. Example: com.android.sample')
argparser.add_argument('apk_file',
                       nargs='?',
                       default='test.apk',
                       help='The path to the APK file to upload.')
argparser.add_argument('--track',
        dest='track',
        action='store',
        default=None,
        help="['alpha', 'beta', 'production', 'rollout']")
argparser.add_argument('--credentials',
        dest='credentials',
        action='store',
        default=None,
        help='Credentials JSON Filename')


def main(argv):
  # Process flags and read their values.
  flags = argparser.parse_args()

  package_name = flags.package_name
  apk_file = flags.apk_file
  track = flags.track
  filename = flags.credentials

  scopes = ['https://www.googleapis.com/auth/androidpublisher']
  credentials = ServiceAccountCredentials.from_json_keyfile_name(
      filename, scopes=scopes)

  http = httplib2.Http()
  http = credentials.authorize(http)

  service = build('androidpublisher', 'v2', http=http)

  if not track in TRACK_OPTIONS:
    print 'Invaild --track option: %s' % track
    return

  try:
    edit_request = service.edits().insert(body={}, packageName=package_name)
    result = edit_request.execute()
    edit_id = result['id']

    apk_response = service.edits().apks().upload(
        editId=edit_id,
        packageName=package_name,
        media_body=apk_file).execute()

    print 'Version code %d has been uploaded' % apk_response['versionCode']

    track_response = service.edits().tracks().update(
        editId=edit_id,
        track=track,
        packageName=package_name,
        body={u'versionCodes': [apk_response['versionCode']]}).execute()

    print 'Track %s is set for version code(s) %s' % (
        track_response['track'], str(track_response['versionCodes']))

    commit_request = service.edits().commit(
        editId=edit_id, packageName=package_name).execute()

    print 'Edit "%s" has been committed' % (commit_request['id'])

  except client.AccessTokenRefreshError:
    print ('The credentials have been revoked or expired, please re-run the '
           'application to re-authorize')

if __name__ == '__main__':
  main(sys.argv)
