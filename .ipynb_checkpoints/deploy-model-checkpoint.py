import subprocess

# --- Variables ---
PROJECT_ID = "super50-19f07"
REGION = "us-central1"
REPO_NAME = "cloud-run-source-deploy"
IMAGE_NAME = "iris"
TAG = "v1"  # change this tag version if needed

# Full Artifact Registry path
IMAGE_PATH = f"{REGION}-docker.pkg.dev/{PROJECT_ID}/{REPO_NAME}/{IMAGE_NAME}:{TAG}"

# --- 1. Build Docker image ---
print(f"Building Docker image: {IMAGE_PATH}")
subprocess.run([
    "docker", "build",
    "-t", IMAGE_PATH,
    "."
], check=True)

# --- 2. Push Docker image ---
print(f"Pushing image to Artifact Registry: {IMAGE_PATH}")
subprocess.run(["docker", "push", IMAGE_PATH], check=True)

# --- 3. Apply Kubernetes manifests ---
for manifest in ["deployment.yaml", "service.yaml", "hpa.yaml"]:
    print(f"Applying {manifest} ...")
    subprocess.run(
        f"env IMAGE={IMAGE_PATH} envsubst < {manifest} | kubectl apply -f -",
        shell=True,
        check=True
    )

print("\n✅ Deployment successful!")
print(f"Deployed image: {IMAGE_PATH}")

