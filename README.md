README:

deploy-model.py – Automates building the Docker image, pushing it to Artifact Registry, and deploying it to Kubernetes.

deployment.yaml – Defines the Kubernetes Deployment for the Iris API, including replicas, container image, and probes.

Dockerfile – Contains instructions to build the Docker image for the FastAPI application and model.

hpa.yaml – Configures the Horizontal Pod Autoscaler to scale pods based on CPU utilization.

main.py – The main FastAPI application that loads the Iris model, handles predictions, and provides health endpoints.

model-server.py – Optional server script to start the FastAPI app or manage model-serving logic.

model-v1.joblib – The pre-trained Iris classification model file.

post.lua – Load testing script used with wrk to simulate multiple concurrent POST requests to the API.

requirements.txt – Lists all Python dependencies required to run the application.

service.yaml – Defines the Kubernetes Service to expose the API through a LoadBalancer.
