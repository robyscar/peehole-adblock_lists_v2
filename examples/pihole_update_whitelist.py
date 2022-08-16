#!/usr/bin/env python3
#
# Download white list and write into Pi-Hole's gravity DB
#
# Implemented for jira-projects/ADBLK#4
#
# For an example of how to deploy this script, see 
# See https://www.bentasker.co.uk/posts/documentation/general/refreshing-piholes-regex-block-list-from-external-sources.html#installation
#

import hashlib
import os
import requests
import subprocess
import sqlite3
import sys


restart_cmd = ["pihole", "restartdns", "reload-lists"]

def fetchList(url):
    ''' Fetch a text file and return a list of lines
    '''
    r = requests.get(url)
    return r.text.split("\n")
    
    
def writeEntries(domain_list,comment):
    ''' Write exact whitelist entries into the gravity database
    '''
    conn = sqlite3.connect("/etc/pihole/gravity.db")
    c = conn.cursor()

    c.execute('DELETE FROM domainlist WHERE comment=?',(comment,))
    c.executemany('INSERT OR IGNORE INTO domainlist (type, domain, comment, enabled) '
                    'VALUES (0, ?, ?, 1)',
                    [(x, comment) for x in sorted(domain_list)])
                    
    conn.commit()
    
# Fetch the whitelist
### whitelist = fetchList('https://raw.githubusercontent.com/bentasker/adblock_lists_v2/master/lists/alloweddomains.txt')
whitelist = fetchList('https://raw.githubusercontent.com/bentasker/adblock_lists_v2/master/lists/alloweddomains.txt')

# Remove empty lines and sort
merged = list(filter(None, whitelist))
whitelist.sort()

# Convert to a string so that we can hash it to check for changes
mergedstr = "\n".join(whitelist)



# Calculate a SHA1
sha1 = hashlib.sha1()
sha1.update(mergedstr.encode('utf-8'))
merged_sha = sha1.hexdigest()

# Initialise for later
cache_sha1 = ""

# Read the cachefile if it exists
if os.path.exists("/etc/pihole/allow_list_cache"):
    with open("/etc/pihole/allow_list_cache") as f:
        cache = f.read()
        sha1 = hashlib.sha1()
        sha1.update(cache.encode('utf-8'))
        cache_sha1 = sha1.hexdigest()
    
# Has the list changed?
if cache_sha1 != merged_sha:
###    writeEntries(whitelist, 'bentasker/adblock_lists_v2/allowlist')
    writeEntries(whitelist, 'bentasker/adblock_lists_v2/allowlist')
    fh = open("/etc/pihole/allow_list_cache", "w")
    fh.write(mergedstr)
    fh.close()
    
    # Restart pihole-FTL
    subprocess.run(restart_cmd, stdout=subprocess.DEVNULL)
    
    # Signal that a change was made
    sys.exit(0)
else:
    # Signal that no change occurred
    sys.exit(2)
