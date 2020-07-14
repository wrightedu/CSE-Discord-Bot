#!/usr/bin/env python3

# Credit goes to Alan Fleming for the module that powers this command
# https://github.com/AlanCFleming/DiceParser

import re
import random


def parse(diceString):
    # Check if diceString is a string
    if not isinstance(diceString, str):
        return

    # Strips trailing and leading whitespace from input
    diceString = diceString.strip().lower()

    # Check if valid string
    if not re.match('^[0-9]*[dD][1-9][0-9]*\s*([+-][0-9]*)?\s*([kKdD][lLhH][0-9]*)?$', diceString):
        return

    # Get the ammount of dice
    ammount = re.search('[0-9]+[dD]', diceString)
    if ammount:
        ammount = int(ammount.group(0)[:-1])
    else:
        ammount = 1

    # Get the type of dice
    sides = re.search('[dD][0-9]+', diceString)
    if sides:
        sides = int(sides.group(0)[1:])

    # Get roll modifier
    mod = re.search('[\+\-][0-9]+', diceString)
    if mod:
        mod = int(mod.group(0))
    else:
        mod = 0

    # Get dice to keep/drop
    keep = re.search('[kKdD][lLhH][0-9]+', diceString)
    if keep:
        # Get ammount to keep/drop
        keepDropAmmount = int(keep.group(0)[2:])
        # Get keeping
        if (keep.group(0)[0:1] == "k"):
            # Get high/low
            if(keep.group(0)[1:2] == "l"):
                high = False
            else:
                high = True
            # Set keep/drop
            keep = True
            drop = False
        # Get dropping
        else:
            # Get high/low
            if(keep.group(0)[1:2] == "l"):
                high = False
            else:
                high = True
            # Set keep/drop
            keep = False
            drop = True
    else:
        keep = False
        drop = False
        high = False
        keepDropAmmount = 0

    if(drop or keep and keepDropAmmount > ammount):
        keepDropAmmount = ammount

    # Roll parsed dice
    return roll(ammount, sides, mod, keep, drop, high, keepDropAmmount)


def roll(ammount, sides, modifier, keep=False, drop=False, high=True, keepDropAmmount=0):

    # Initialize list
    rollList = []

    # Generate all rolls
    for i in range(0, ammount):
        rollList.append(random.randint(1, sides))

    # Sort the rolls
    rollList = sorted(rollList) if high else sorted(rollList, reverse=True)

    if(keep):
        # Initialize list of rolls to keep
        keepList = []
        # Pull out rolls to keep
        for i in range(0, keepDropAmmount):
            keepList.append(rollList.pop())
        # Pint adjusted rolls
        return (keepList, (sum(keepList) + modifier), rollList)
    elif(drop):
        # Initialize list of rolls to keep
        dropList = []
        # Pull out rolls to keep
        for i in range(0, keepDropAmmount):
            dropList.append(rollList.pop())
        return (rollList, (sum(rollList) + modifier), dropList)
    else:
        return (rollList, (sum(rollList) + modifier), [])


# Main function to runn if file is called directly
if __name__ == '__main__':
    diceString = ''
    while(True):
        # Get the users input
        diceString = input().lower()
        # Exit program on input being exit
        if (diceString == "exit"):
            break
        # Pass input to parser
        parse(diceString)
        # Line brike for rolls
