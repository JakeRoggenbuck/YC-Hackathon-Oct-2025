# YC-Hackathon-Oct-2025

## Design

<img width="1252" height="665" alt="image" src="https://github.com/user-attachments/assets/ce4d196f-9c06-4c81-98d6-d50e7e725214" />

## Components

#### 1. Frontend - Command and Control

Uses Replit and React JS. Used to configure and start your agents.

#### 2. Backend - Agent Manager

Written in Python using FastAPI to start agents when requested from the frontend. Also responsible for running the Email Summary Service.

#### 3. Email Summary Service

Send an email summary with Agent Mail. 

#### 4. The Agents

We will use Mastral to write our agents. They will use Moss, Convex, and Hyperspell for their searching and memory.

They will use the provided API url and look for a openapi.json to know what routes to call. It can remember this with Hyperspell.

The semantic search with the source aware GitHub pulling. If we want to test an endpoint called "/test", we can use either Moss or Convex to pull up the relevant code to augment our result.
