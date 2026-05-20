/**
 * pi-deploy - 自动化部署
 */

import type { ExtensionAPI } from "@mariozechner/pi-coding-agent";
import { writeFile, mkdir } from "fs/promises";
import { join } from "path";
import { spawn } from "child_process";

const DOCKERFILE = `
FROM node:20-alpine
WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production
COPY . .
EXPOSE 3000
CMD ["node", "index.js"]
`;

const DOCKER_COMPOSE = `
version: '3.8'
services:
  app:
    build: .
    ports:
      - "3000:3000"
    restart: unless-stopped
`;

const GITHUB_WORKFLOW = `
name: Deploy

on:
  push:
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
    - name: Install
      run: npm ci
    - name: Build
      run: npm run build
    - name: Test
      run: npm test
`;

async function runCmd(cmd: string, args: string[]): Promise<string> {
  return new Promise((resolve) => {
    const proc = spawn(cmd, args, { shell: true });
    let output = "";
    proc.stdout?.on("data", (d) => { output += d.toString(); });
    proc.on("close", (code) => { resolve(output || `完成 (exit: ${code})`); });
    proc.on("error", (err) => { resolve(`失败: ${err.message}`); });
  });
}

export default function (pi: ExtensionAPI): void {
  pi.registerCommand("deploy", {
    description: "自动化部署 (docker, ci, k8s, vercel, railway)",
    handler: async (args: string) => {
      const projectPath = process.cwd();
      
      if (args.includes("--docker")) {
        try {
          await writeFile(join(projectPath, "Dockerfile"), DOCKERFILE.trim(), "utf-8");
          await writeFile(join(projectPath, "docker-compose.yml"), DOCKER_COMPOSE.trim(), "utf-8");
          await writeFile(join(projectPath, ".dockerignore"), "node_modules\n.git\ndist\ncoverage\n*.log\n", "utf-8");
          return `Docker 配置已生成:\n- Dockerfile\n- docker-compose.yml\n- .dockerignore\n\n构建: docker build -t myapp .\n运行: docker-compose up`;
        } catch (err: any) {
          return `生成失败: ${err.message}`;
        }
      }
      
      if (args.includes("--ci")) {
        try {
          await mkdir(join(projectPath, ".github", "workflows"), { recursive: true });
          await writeFile(join(projectPath, ".github", "workflows", "deploy.yml"), GITHUB_WORKFLOW.trim(), "utf-8");
          return `CI/CD 配置已生成:\n- .github/workflows/deploy.yml\n\n推送到 main 分支自动触发`;
        } catch (err: any) {
          return `生成失败: ${err.message}`;
        }
      }
      
      if (args.includes("--k8s")) {
        try {
          await mkdir(join(projectPath, "k8s"), { recursive: true });
          await writeFile(join(projectPath, "k8s", "deployment.yaml"), `
apiVersion: apps/v1
kind: Deployment
metadata:
  name: app
spec:
  replicas: 3
  selector:
    matchLabels:
      app: app
  template:
    metadata:
      labels:
        app: app
    spec:
      containers:
      - name: app
        image: app:latest
        ports:
        - containerPort: 3000
`, "utf-8");
          await writeFile(join(projectPath, "k8s", "service.yaml"), `
apiVersion: v1
kind: Service
metadata:
  name: app
spec:
  type: LoadBalancer
  selector:
    app: app
  ports:
  - port: 80
    targetPort: 3000
`, "utf-8");
          return `K8s 配置已生成:\n- k8s/deployment.yaml\n- k8s/service.yaml`;
        } catch (err: any) {
          return `生成失败: ${err.message}`;
        }
      }
      
      if (args.includes("--vercel")) {
        return await runCmd("npx", ["vercel", "--yes"]);
      }
      
      if (args.includes("--railway")) {
        return await runCmd("npx", ["railway", "up"]);
      }
      
      return `部署命令:\n/deploy --docker   # Dockerfile + docker-compose\n/deploy --ci      # GitHub Actions\n/deploy --k8s     # Kubernetes 配置\n/deploy --vercel  # Vercel 部署\n/deploy --railway # Railway 部署`;
    }
  });
}
