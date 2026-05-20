#!/bin/bash
cd /d
git clone https://github.com/hsliuping/TradingAgents-CN.git TradingAgents-CN
cd TradingAgents-CN
python -m venv venv
source venv/Scripts/activate
pip install -r requirements.txt
cp .env.example .env
