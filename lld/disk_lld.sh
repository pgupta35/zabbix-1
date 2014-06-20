#!/bin/bash

listcontains() {
  for word in $1; do
    [[ $word = $2 ]] && return 0
  done
  return 1
}

OUTPUT='{"data":[ '
FIRST=1

## read sd* exclude list from config file (don't need in most cases)
BLACKLIST_CFG=$(readlink -f "$(dirname $0)/disk_lld.blacklist")
if [[ -e "$BLACKLIST_CFG" ]] ; then
  BLACKLIST=$(<"$BLACKLIST_CFG")
else
  BLACKLIST=
fi

## discover DM devices, output mpathX raw devices only (exclude partitions and LVM LV)
for d in /sys/block/dm-*; do
  ID=$(basename $d)
  DMNAME=$(cat $d/dm/name)
  DMUUID=$(cat $d/dm/uuid)
  NAME="$DMNAME"

  #NAME="${NAME} ($(echo $(for h in $d/holders/dm-*/dm/name; do if [[ -e $h ]] ; then cat $h; fi; done)))"

  if [[ "$DMUUID" =~ ^mpath-+* ]] ; then
    if [[ -e "$d/slaves" ]] ; then 
      BLACKLIST="$BLACKLIST $(echo $(ls $d/slaves))"
    fi

    if ((FIRST)); then FIRST=0; else OUTPUT="${OUTPUT}, "; fi
    OUTPUT=${OUTPUT}'{"{#ID}":"'$ID'","{#NAME}":"'$NAME'"}'
  fi
done

## discover sd* devices, don't output mpath slaves and blackisted in BLACKLIST_CFG
for d in /sys/block/sd*; do
  ID=$(basename $d)
  NAME="$ID"
  if !(listcontains "$BLACKLIST" $ID); then
    if ((FIRST)); then FIRST=0; else OUTPUT="${OUTPUT}, "; fi
    OUTPUT=${OUTPUT}'{"{#ID}":"'$ID'","{#NAME}":"'$ID'"}'
  fi
done

OUTPUT="${OUTPUT} ]}"
echo "$OUTPUT"
