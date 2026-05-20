Set-Location D:\
if (-not (Test-Path "TradingAgents-CN")) {
    Write-Host "Cloning repository..."
    git clone https://github.com/hsliuping/TradingAgents-CN.git TradingAgents-CN
} else {
    Write-Host "Directory already exists"
}
Set-Location D:\TradingAgents-CN
Write-Host "Creating virtual environment..."
python -m venv venv
Write-Host "Activating virtual environment..."
.\venv\Scripts\Activate.ps1
Write-Host "Installing dependencies..."
pip install -r requirements.txt
Write-Host "Copying .env.example to .env..."
Copy-Item .env.example .env -Force
Write-Host "Done!"
