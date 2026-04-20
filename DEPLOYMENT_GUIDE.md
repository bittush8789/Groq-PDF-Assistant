# 🚀 End-to-End Deployment & Tooling Guide

This guide provides a comprehensive walkthrough for setting up, containerizing, and deploying the **DocuQA** application to a production-like environment using Kubernetes and GitOps.

---

## 🛠️ Tool Installation Guide

### 1. Docker & Docker Compose
- **Windows/Mac**: Install [Docker Desktop](https://www.docker.com/products/docker-desktop/).
- **Linux**:
  ```bash
  sudo apt update && sudo apt install docker.io docker-compose -y
  sudo usermod -aG docker $USER && newgrp docker
  ```

### 2. Kubernetes CLI (kubectl)
- **Windows (Chocolatey)**: `choco install kubernetes-cli`
- **Mac (Homebrew)**: `brew install kubectl`
- **Linux**:
  ```bash
  curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
  chmod +x kubectl && sudo mv kubectl /usr/local/bin/
  ```

### 3. Local K8s Cluster (Kind)
- **Installation**:
  ```bash
  # Mac/Linux (Binary)
  curl -Lo ./kind https://kind.sigs.k8s.io/dl/v0.20.0/kind-linux-amd64
  chmod +x ./kind && sudo mv ./kind /usr/local/bin/
  ```

### 4. ArgoCD CLI
- **Installation**:
  ```bash
  curl -sSL -o argocd-linux-amd64 https://github.com/argoproj/argo-cd/releases/latest/download/argocd-linux-amd64
  sudo install -m 555 argocd-linux-amd64 /usr/local/bin/argocd
  rm argocd-linux-amd64
  ```

---

## 🚀 Step-by-Step Execution Guide

### Step 1: Clone & Configure
```bash
git clone https://github.com/bittush8789/Groq-PDF-Assistant.git
cd Groq-PDF-Assistant

# Create .env file
cat <<EOF > .env
GEMINI_API_KEY=your_gemini_key
GROQ_API_KEY=your_groq_key
EOF
```

### Step 2: Local Development
```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

### Step 3: Containerization
```bash
# Build the production image
docker build -t docuqa-app:v1 .

# Run locally via Docker
docker run -p 8501:8501 --env-file .env docuqa-app:v1
```

### Step 4: Kubernetes (Kind) Deployment
```bash
# 1. Create Cluster
kind create cluster --name docuqa-cluster

# 2. Load Image into Kind
kind load docker-image docuqa-app:v1 --name docuqa-cluster

# 3. Create Namespace
kubectl create namespace docuqa

# 4. Apply Manifests
kubectl apply -f k8s/resources.yaml
kubectl apply -f k8s/deployment.yaml

# 5. Verify & Access
kubectl get all -n docuqa
kubectl port-forward svc/docuqa-service 8501:80 -n docuqa
```

### Step 5: Setup GitOps (ArgoCD)
```bash
# 1. Install ArgoCD
kubectl create namespace argocd
kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml

# 2. Access UI
kubectl port-forward svc/argocd-server -n argocd 8080:443

# 3. Deploy Application
kubectl apply -f argocd/application.yaml
```

---

## 📊 Observability & Maintenance
- **Check Logs**: `kubectl logs -l app=docuqa -n docuqa`
- **Check Health**: `curl http://localhost:8501/_stcore/health`
- **Scale Up**: `kubectl scale deployment streamlit-app --replicas=3 -n docuqa`
