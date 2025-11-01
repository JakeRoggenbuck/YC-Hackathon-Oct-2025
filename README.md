# YC-Hackathon-Oct-2025

**Agentically scan for bugs in FastAPI backend servers.**

[![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![TypeScript](https://img.shields.io/badge/typescript-%23007ACC.svg?style=for-the-badge&logo=typescript&logoColor=white)](https://www.typescriptlang.org/)

![Static Badge](https://img.shields.io/badge/Convex-orange?style=for-the-badge)
![Static Badge](https://img.shields.io/badge/Moss-purple?style=for-the-badge)
![Static Badge](https://img.shields.io/badge/AgentMail-orange?style=for-the-badge)
![Static Badge](https://img.shields.io/badge/Mastra-purple?style=for-the-badge)
![Static Badge](https://img.shields.io/badge/Hyperspell-orange?style=for-the-badge)

We use [Moss](https://www.usemoss.dev/) (Sematic search), [Convex](https://www.convex.dev/) (State for agents), [AgentMail](https://agentmail.to/) (Email updates), [Mastra](https://mastra.ai) (Agents), [Perplexity](https://www.perplexity.ai/) (TODO: Email generation), [Replit](https://replit.com/) (Frontend)

## Contributors

TODO

## Design

General system design

<img width="3380" height="1902" alt="agentic api bug finder" src="https://github.com/user-attachments/assets/1cd6f365-456f-4bf8-93be-07afba777e67" />

Backend system design

![img_3529](https://github.com/user-attachments/assets/63ea2c70-2147-446b-b826-e6cda80aa182)

More components

<img width="1410" height="764" alt="image" src="https://github.com/user-attachments/assets/1ac0764f-8e39-49af-9697-6b6539c23078" />

## Components

#### 1. Frontend - Command and Control

Uses Replit and React JS. Used to configure and start your agents.

#### 2. Backend - Agent Manager

Written in Python using FastAPI to start agents when requested from the frontend. Also responsible for running the Email Summary Service.

[Backend Docs](https://github.com/JakeRoggenbuck/YC-Hackathon-Oct-2025/tree/main/backend).

**POST** `/start-agent`

Starts an agent with the provided configuration.

## Request Body

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `email` | string | Yes | Valid email address |
| `hosted_api_url` | string | Yes | URL of the hosted API |
| `github_repo` | string | Yes | GitHub repository URL |

#### 3. Email Summary Service

Send an email summary with Agent Mail.

##### Email on startup

<img width="1634" height="892" alt="image" src="https://github.com/user-attachments/assets/8fd3fa7e-0b13-40f0-8e5d-b24fef088172" />

##### Email when agent is done

<img width="1602" height="870" alt="image" src="https://github.com/user-attachments/assets/8d0020a1-1ac8-460d-af8b-c0c9ba2836a6" />

#### 4. The Agents

We will use [Mastra](https://mastra.ai) to write our agents. They will use [Moss](https://www.usemoss.dev/), Convex, and Hyperspell for their searching and memory.

They will use the provided API url and look for a openapi.json to know what routes to call. It can remember this with Hyperspell.

The semantic search with the source aware GitHub pulling. If we want to test an endpoint called "/test", we can use either Moss or Convex to pull up the relevant code to augment our result.

#### Engineering Notes
- Max of 500 .py files in Moss agent for now, can be scaled later but kept at a respectable size right now to minimize system latency.

##### Why use Convex?
- Uses a queue system to keep agent state
- Our Mastra agents are in typescript and backend is in python. We would already need a HTTP server anyways, might as well use Convx as a queue for fast data retrieval.
- We can use Reactive Queries where the Agents can subscribe to queue changes in real-time

<img width="721" height="738" alt="image" src="https://github.com/user-attachments/assets/adc30cd0-29e2-416f-840c-129bc9b849be" />


