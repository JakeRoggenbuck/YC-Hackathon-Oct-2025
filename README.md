# YC-Hackathon-Oct-2025

## Contributors

TODO

## Design

<img width="3380" height="1902" alt="agentic api bug finder" src="https://github.com/user-attachments/assets/1cd6f365-456f-4bf8-93be-07afba777e67" />

## Components

#### 1. Frontend - Command and Control

Uses Replit and React JS. Used to configure and start your agents.

#### 2. Backend - Agent Manager

Written in Python using FastAPI to start agents when requested from the frontend. Also responsible for running the Email Summary Service.

#### 3. Email Summary Service

Send an email summary with Agent Mail. 

#### 4. The Agents

We will use [Mastra](https://mastra.ai) to write our agents. They will use [Moss](https://www.usemoss.dev/), Convex, and Hyperspell for their searching and memory.

They will use the provided API url and look for a openapi.json to know what routes to call. It can remember this with Hyperspell.

The semantic search with the source aware GitHub pulling. If we want to test an endpoint called "/test", we can use either Moss or Convex to pull up the relevant code to augment our result.

#### Engineering Notes
- Max of 500 .py files in Moss agent for now, can be scaled later but kept at a respectable size right now to minimize system latency.