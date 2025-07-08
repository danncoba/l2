# Matrix validation introduction

Generate an evaluation dataset for evaluating AI application consisting of the following schema:
```json
{
    "discrepancy": {
      "grade_id": 1,
      "skill_id": 1,
      "user_id": 1
    },
    "guidance": [],
    "next_steps": [],
    "messages": [
      {
        "message": "Some message", // value to send
        "role": "some_agent" // can be any string representing AI agent
      }
    ],
    "chat_messages": [
      {
        "message": "Message between ai and user",
        "role": "ai" // either ai or user
      }
    ] 
}
```
## Goal
reate an evaluation dataset that follows the schema above. Evaluation dataset will evaluate the precision of
AI application that correctly guides the user through self-evaluation process.

First message must be from AI asking the user about their expertise within a specific tech based area

The message should look like the following example. Always use the same format of the message, just change the tech
subject of the discussion and the user that is being asked to self evaluate

**Example**:
```text
Expertise Levels in Backup and Recovery
Welcome! In this discussion, we will explore the various expertise levels related to the skill of Backup and Recovery. Understanding these levels will help you select the appropriate expertise that aligns with your current knowledge and experience.

Here are the available expertise grades:

Not Informed: You have no prior knowledge of the topic.
Informed Basics: You understand the basic concepts of Backup and Recovery.
Informed in Details: You have a deeper understanding of the strategies involved.
Practice and Lab Examples: You can apply your knowledge through practical examples and lab work.
Production Maintenance: You are capable of maintaining backup systems in a production environment.
Production from Scratch: You can set up backup systems from the ground up.
Educator/Expert: You possess extensive knowledge and can teach others about Backup and Recovery.
Consider your current level of understanding and experience to choose the expertise that best fits you. This will enhance your learning and engagement in our discussion!
```

After this initial AI message, each message should be zig zag between user than AI etc.....


## Schema explanation
#### Discrepancy
This has 3 grades within it. Users id to search by, grade id that it is the newly selected grade and skill id represents the skill we
are self evaluating. These id's are used for subsequent tools, so always include them
#### Guidance
Keep this empty for now, an empty array!
#### Next Steps
Keep this empty as of now, ann empty array
#### Messages
Keep this empty for now as well, we will add this later. This represents supervisor internal discussion with other
agents to get to the final discussion. We will be populating this later
#### Chat Messages
This is where AI message and human messages are consistently propagated, and this needs to follow the above example. Each of
the elements should have a message containing the similar message as in the example and role (either ai or human)
You should have as many messages in this array as the discussion is lasting

