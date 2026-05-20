/**
 * Pi Deploy - 自动化部署
 */

import { writeFile, mkdir } from "fs/promises";
import { join } from "path";

export interface DeployOptions {
  name: string;
  port?: number;
  healthCheck?: string;
}

const DOCKERFILE_TEMPLATE = (options: DeployOptions) => `
FROM node:20-alpine

WORKDIR /app

COPY package*.json ./
RUN npm ci --only=production

COPY . .

EXPOSE ${options.port || 3000}

CMD ["node", "index.js"]
`;

const DOCKER_COMPOSE_TEMPLATE = (options: DeployOptions) => `
version: '3.8'

services:
  app:
    build: .
    ports:
      - "${options.port || 3000}:${options.port || 3000}"
    restart: unless-stopped
    ${options.healthCheck ? `
    healthcheck:
      test: ["CMD", "curl", "-f", "${options.healthCheck}"]
      interval: 30s
      timeout: 10s
      retries: 3
    ` : ''}
`;

const K8S_DEPLOYMENT_TEMPLATE = (options: DeployOptions) => `
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ${options.name}
  labels:
    app: ${options.name}
spec:
  replicas: 3
  selector:
    matchLabels:
      app: ${options.name}
  template:
    metadata:
      labels:
        app: ${options.name}
    spec:
      containers:
      - name: ${options.name}
        image: ${options.name}:latest
        ports:
        - containerPort: ${options.port || 3000}
`;

const K8S_SERVICE_TEMPLATE = (options: DeployOptions) => `
apiVersion: v1
kind: Service
metadata:
  name: ${options.name}
spec:
  type: LoadBalancer
  selector:
    app: ${options.name}
  ports:
  - port: 80
    targetPort: ${options.port || 3000}
`;

const GITHUB_ACTIONS_TEMPLATE = `
name: Deploy

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  build-and-deploy:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v4
    
    - name: Setup Node.js
      uses: actions/setup-node@v4
      with:
        node-version: '20'
        
    - name: Install dependencies
      run: npm ci
      
    - name: Build
      run: npm run build
      
    - name: Test
      run: npm test
      
    - name: Deploy
      run: |
        # Add your deployment commands here
        echo "Deploying..."
`;

export async function generateDockerfile(
  projectPath: string,
  options: DeployOptions
): Promise<void> {
  const file = join(projectPath, "Dockerfile");
  await writeFile(file, DOCKERFILE_TEMPLATE(options), "utf-8");
  
  const composeFile = join(projectPath, "docker-compose.yml");
  await writeFile(composeFile, DOCKER_COMPOSE_TEMPLATE(options), "utf-8");
}

export async function generateK8s(
  projectPath: string,
  options: DeployOptions
): Promise<void> {
  const k8sDir = join(projectPath, "k8s");
  await mkdir(k8sDir, { recursive: true });
  
  await writeFile(join(k8sDir, "deployment.yaml"), K8S_DEPLOYMENT_TEMPLATE(options), "utf-8");
  await writeFile(join(k8sDir, "service.yaml"), K8S_SERVICE_TEMPLATE(options), "utf-8");
}

export async function generateGitHubActions(projectPath: string): Promise<void> {
  const workflowDir = join(projectPath, ".github", "workflows");
  await mkdir(workflowDir, { recursive: true });
  
  await writeFile(join(workflowDir, "deploy.yml"), GITHUB_ACTIONS_TEMPLATE, "utf-8");
}

export async function deployToVercel(projectPath: string): Promise<void> {
  const { spawn } = await import("child_process");
  
  return new Promise((resolve, reject) => {
    const proc = spawn("npx", ["vercel", "--prod"], {
      cwd: projectPath,
      stdio: "inherit"
    });
    
    proc.on("close", (code) => {
      if (code === 0) resolve();
      else reject(new Error(`Deploy failed with code ${code}`));
    });
  });
}

export async function deployToRailway(projectPath: string): Promise<void> {
  const { spawn } = await import("child_process");
  
  return new Promise((resolve, reject) => {
    const proc = spawn("npx", ["railway", "up"], {
      cwd: projectPath,
      stdio: "inherit"
    });
    
    proc.on("close", (code) => {
      if (code === 0) resolve();
      else reject(new Error(`Deploy failed with code ${code}`));
    });
  });
}
