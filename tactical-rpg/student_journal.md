# Introduction
Hello! I am writing in here to give my thoughts and takeaways as to what I have learned with this project and any interesting takeaways I might have.
# What I Learned
I wanted this project to be something that I could learn from in terms of developing and testing a game, since that is something that I want to pursue.
However with that comes challenges, especially when working with AI like Claude Code in order to develop the scripts of the game.
One thing that I've learned when it comes to agentic coding like this: **Be Specific.** Claude Code will program something out
for you, however it takes everything you say in a *literal* sense. For instance: I wanted to use ripped sprite sheets that I found
from the GameBoy Advanced Fire Emblem games, they all came in .gif formats so I asked Claude Code to develop with that in mind.
This caused a massive headache because it was cropping the files, and since they weren't all exactly the same formatting
the code was getting messed up and making the sprites look worse than they are.

If Claude is good at one thing, it is taking what you say to it and making it in a way that *works* but might not be perfect. 
Become accustomed to checking your work, as making sure that your program is working fine is important. Also, **Test thoroughly.**
I've had many cases during this process where I would find a completely unrelated bug because I never thought to test the bug out beforehand.
This was seen firsthand for me when, a dozen prompts and a couple hours after I implemented items, it turned out the items menu *didn't work at all*.

Moral of the story: Be specific, test thoroughly.
# Interesting Takeaways
This project was a lot more in depth and interactive with myself as the "prompter" which was fun. It was mostly sorting files
and getting assets for claude to use while it worked on the scripts. One takeaway that I have from this project is that Claude
works perfectly as a tool to make your scripts, however you shouldn't have it work on super complicated stuff. I learned this
because of the .gif sprite sheets I was previously using, the agent was having a tough time making it work so I swapped over to
PNG's instead and now it is doing fantastic. 

I also learned how important it is to tell your agent to rerun your tests, as I was making the agent rerun tests over and over
and every time it found some new bug that I would've never expected or some code that wasn't being used.