#!/usr/bin/env python3
#
# Download zone and regex lists, format them and write into Pi-Hole's gravity DB
#
# Older versions of pihole used regex.list, this script works with more recent versions
# where the gravity DB needs to be manually updated
#
# Older versions can use https://github.com/bentasker/adblocklists/blob/master/bin/pihole_apply_regexes.sh
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
    
    
def writeRegexes(regex_list,comment):
    ''' Write regexes into the gravity database
    '''
    conn = sqlite3.connect("/etc/pihole/gravity.db")
    c = conn.cursor()

    c.execute('DELETE FROM domainlist WHERE comment=?',(comment,))
    c.executemany('INSERT OR IGNORE INTO domainlist (type, domain, comment, enabled) '
                    'VALUES (3, ?, ?, 1)',
                    [(x, comment) for x in sorted(regex_list)])
                    
    conn.commit()
    
    
def fetchZoneList(url):
    ''' Fetch the list of zones and translate into regexes
    '''
    t = fetchList(url)
    
    # Currently just a domain list, we need to turn it them into regexes
    regexes = []
    for line in t:
        # Ignore empty lines
        if line == "":
            continue
        
        regex = line.replace(".","\.")
        regexes.append(f"^{regex}$")
        regexes.append(f"^.+\.{regex}$")
        
    return regexes
    

# Fetch the two lists
### regexes = fetchList('https://raw.githubusercontent.com/bentasker/adblock_lists_v2/master/lists/regexes.txt')
### zones = fetchZoneList("https://raw.githubusercontent.com/bentasker/adblock_lists_v2/master/lists/zones.txt")

regexes = fetchList('https://raw.githubusercontent.com/bentasker/adblock_lists_v2/master/lists/regexes.txt')
zones = fetchZoneList("https://raw.githubusercontent.com/bentasker/adblock_lists_v2/master/lists/zones.txt")



# Merge them and remove any empty values
merged = list(filter(None, regexes + zones))

# De-dupe and sort
merged = list(set(merged))
merged.sort()

# Convert to a string so that we can hash it to check for changes
mergedstr = "\n".join(merged)

# Calculate a SHA1
sha1 = hashlib.sha1()
sha1.update(mergedstr.encode('utf-8'))
merged_sha = sha1.hexdigest()

# Initialise for later
cache_sha1 = ""

# Read the cachefile if it exists
if os.path.exists("/etc/pihole/regex_list_cache"):
    with open("/etc/pihole/regex_list_cache") as f:
        cache = f.read()
        sha1 = hashlib.sha1()
        sha1.update(cache.encode('utf-8'))
        cache_sha1 = sha1.hexdigest()
    
# Has the list changed?
if cache_sha1 != merged_sha:
    writeRegexes(merged,'bentasker/adblock_lists_v2')
    fh = open("/etc/pihole/regex_list_cache", "w")
    fh.write(mergedstr)
    fh.close()
    
    # Restart pihole-FTL
    subprocess.run(restart_cmd, stdout=subprocess.DEVNULL)
    
    # Signal that a change was made
    sys.exit(0)
else:
    # Signal that no change occurred
    sys.exit(2)
