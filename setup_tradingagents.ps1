# TradingAgents-CN 项目设置说明

## 问题说明
当前环境的 bash 命令执行遇到问题，无法直接执行 git 等命令。

## 已创建的脚本

### 1. setup_tradingagents.bat (推荐 Windows 用户使用)
路径: `D:\pi-coding-agent\setup_tradingagents.bat`

双击运行即可完成以下步骤：
- 克隆仓库到 D:\TradingAgents-CN
- 创建 Python 虚拟环境
- 安装依赖
- 配置 .env 文件

### 2. setup_trading.sh (如使用 Git Bash 或 WSL)
路径: `D:\pi-coding-agent\setup_trading.sh`

## 手动执行命令

如果脚本无法运行，请打开命令提示符 (CMD) 并依次执行：

```cmd
# 1. 克隆仓库
git clone https://github.com/hsliuping/TradingAgents-CN.git D:\TradingAgents-CN

# 2. 进入目录
cd D:\TradingAgents-CN

# 3. 创建虚拟环境
python -m venv venv

# 4. 激活虚拟环境
venv\Scripts\activate

# 5. 安装依赖
pip install -r requirements.txt

# 6. 复制环境配置
copy .env.example .env

# 7. 编辑 .env 配置 API 密钥
notepad .env

# 8. 查看 README 了解启动方式
type README.md
```

## 启动应用

根据项目结构，常见的启动方式包括：

```cmd
# 方法1: Streamlit Web 界面
streamlit run app/main.py

# 方法2: 直接运行主程序
python main.py

# 方法3: Docker 方式
docker-compose up
```

## 项目信息

- **项目**: TradingAgents-CN (中文增强版)
- **描述**: 基于多智能体LLM的中文金融交易框架
- **语言**: Python
- **Stars**: 23,000+
- **官方文档**: https://github.com/hsliuping/TradingAgents-CN
