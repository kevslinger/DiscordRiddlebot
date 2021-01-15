# Riddlebot for Discord!
 
[![Build Status](https://travis-ci.com/kevslinger/DiscordRiddlebot.svg?branch=main)](https://travis-ci.com/kevslinger/DiscordRiddlebot)

A simple python riddlebot for discord, using Google Sheets and Heroku

## Current Comamnds
- `?riddle` gives a riddle
- `?answer answer` will get the bot to check your guess against the correct answer
- `?hint` will give a hint for the riddle, if applicable
- `?showanswer` will show the answer, and end the riddle
- `?forceriddle` will force the bot to end the current riddle and get a new one.
- `?addriddle` will give the user a link to a Google Form where they can submit more riddles to be added

`bot.py` starts up the bot, and all the code for the commands can be found in the `modules` directory.

