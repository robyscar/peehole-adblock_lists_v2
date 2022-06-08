#!/bin/bash
#
# Build the output lists
#
# First added in jira-projects/ADBLK#1

function blockdomain(){
    domain=$1
    echo "$domain" >> $blocked_doms


    # Check if the domain exists within a zone that'll be blocked
    egrep -v -e "^${domain#*.}|^$domain" $blocked_zones > /dev/null
    if [ "$?" == "1" ]
    then
        echo "local-data: \"$domain A 127.0.0.1\"" >> $unbound_listbuild
        echo "local-data: \"$domain AAAA ::1\"" >> $unbound_listbuild
    fi
}


function buildZoneList(){
    # Build the zones derived lists
    
    # Take the manualzones
    cat config/manualzones.txt | egrep -v -e '^#' | while read -r domain
    do
        echo "$domain" >> $blocked_zones
        echo "$domain"
    done

    # TODO: the original looked for domains in blockedpages.txt - might want to include that
    
    
    # Take the list of blocked zones and turn it into unbound format
    cat $blocked_zones | sort | uniq | egrep -v -e '^$' | while read -r domain
    do
        echo "local-zone: \"$domain\" redirect" >> $unbound_listbuild
        echo "local-data: \"$domain A 127.0.0.1\"" >> $unbound_listbuild
    done
}

# Create a temporary file for each of the lists

# Compiled temporary domain list
domain_listtmp=`mktemp`

# Unbound format
unbound_listbuild=`mktemp`

# Domain list
blocked_doms=`mktemp`

# Blocked Zones (TODO)
blocked_zones=`mktemp`

# ABP (TODO)
abp=`mktemp`


buildZoneList

for blockfile in config/manualblocks/*txt 
do
    cat $blockfile | egrep -v -e '^#|^$' | while read -r domain
    do
        echo "$domain" >> $domain_listtmp
        echo "$domain"
    done
done


cat $domain_listtmp | sort | uniq | egrep -v -e '^$' | while read -r domain
do
    blockdomain $domain
done




cat << EOM

============== List $domain_listtmp ===========
`cat $domain_listtmp`


============== Unbound ===========
`cat $unbound_listbuild`


============== Zones ==============
`cat $blocked_zones`

EOM
