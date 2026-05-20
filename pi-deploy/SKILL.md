---
name: pi-deploy
description: 自动化部署。生成 Dockerfile、CI/CD、K8s 配置，支持 Vercel、Railway 部署。
---

# pi-deploy

自动化部署扩展，通过 `/deploy` 命令。

## 命令

```
/deploy --docker    # 生成 Dockerfile + docker-compose
/deploy --ci       # 生成 GitHub Actions 配置
/deploy --k8s      # 生成 Kubernetes 配置
/deploy --vercel   # 部署到 Vercel
/deploy --railway  # 部署到 Railway
```

## 生成文件

### Docker
```
/deploy --docker
```
生成:
- `Dockerfile`
- `docker-compose.yml`
- `.dockerignore`

### CI/CD
```
/deploy --ci
```
生成:
- `.github/workflows/deploy.yml`

### Kubernetes
```
/deploy --k8s
```
生成:
- `k8s/deployment.yaml`
- `k8s/service.yaml`

## 示例

```
/deploy --docker
/deploy --ci
/deploy --k8s
```
