# Frontend - Command and Control Interface

React/TypeScript web application for configuring and starting API testing agents.

## Tech Stack

- **React 18** with TypeScript
- **Vite** for build tooling
- **Wouter** for routing
- **TanStack Query** for API state management
- **shadcn/ui** components (Radix UI + Tailwind CSS)
- **React Hook Form** with Zod validation

## Getting Started

```bash
npm install
npm run dev
```

To run convex ``` npx convex dev ```

The application will start on `http://localhost:5173` (or your configured port).

## Project Structure

```
frontend/
├── client/              # React application
│   ├── src/
│   │   ├── components/  # UI components (forms, buttons, etc.)
│   │   ├── pages/       # Route pages
│   │   └── lib/         # Utilities and client config
└── package.json
```

## Features

- **Testing Form**: Submit API endpoints, GitHub repositories, and email addresses
- **Agent Configuration**: Start agents with custom parameters via the backend API
- **Success Notifications**: Visual feedback when agents are successfully started

## Environment Variables

Configure the backend API endpoint if needed (defaults to `http://localhost:8000`).

