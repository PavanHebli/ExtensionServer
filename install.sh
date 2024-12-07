# install anaconda 
echo "[INFO] installing anaconda"
curl -O https://repo.anaconda.com/archive/Anaconda3-2024.10-1-Linux-x86_64.sh
shasum -a 256 ~/Anaconda3-2024.10-1-Linux-x86_64.sh
bash ~/Anaconda3-2024.10-1-Linux-x86_64.sh
source ~/.bashrc

echo "[INFO] installing source code and dependencies"
# download the source code from github
git clone https://github.com/PavanHebli/ExtensionServer.git
cd ExtensionServer
pip3 install -r requirements.txt

echo "[INFO] downloading ollama server"
curl -fsSL https://ollama.com/install.sh | sh
