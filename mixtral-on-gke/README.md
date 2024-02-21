# Mistral on GKE

This example will demostrate how to serve [Mixtral 8X7B](https://mistral.ai/news/mixtral-of-experts/ "Mixtral 8X7B") model on [NVIDIA L4 GPUs](https://cloud.google.com/compute/docs/gpus#l4-gpus "NVIDIA L4 GPUs") running on Google Cloud Kubernetes Engine (GKE). It will help you understand the AI/ML ready features of GKE and how to use them to serve large language models.

## What is Mistral?

Mixtral 8X7B is the latest LLM provided by [Mistral.ai](https://mistral.ai "Mistral.ai")


## Building on Kubernetes

### Setting Environment Variable

Before we get started, we are going to set some environment variables. This is just to make our lives easier as we are going through the process of building our infrastucture. 

```bash
export PROJECT_ID=<your-project-id>
export REGION=<your region>
export ZONE_1=${REGION}-b 
export ZONE_2=${REGION}-c
export CLUSTER_NAME=llm-serving-cluster
export NETWORK=<your network> #the "default" network works
gcloud config set project "$PROJECT_ID"
gcloud config set compute/region "$REGION"
gcloud config set compute/zone "$ZONE_1"
```

You will want to replace `<your-project-id>` with you actual progrect. You will also do this with the region you desire. I defaulted the zones to `b` and `c` but you are able to change it to whatever you choose.

We also need to enable to project APIs

```bash
gcloud services enable compute.googleapis.com container.googleapis.com
```


```bash
PROJECT_NUMBER=$(gcloud projects describe $PROJECT_ID --format='value(projectNumber)')
GCE_SA="${PROJECT_NUMBER}-compute@developer.gserviceaccount.com"

gcloud projects add-iam-policy-binding $PROJECT_ID \
--member=serviceAccount:${GCE_SA} --role=roles/monitoring.metricWriter
gcloud projects add-iam-policy-binding $PROJECT_ID \
--member=serviceAccount:${GCE_SA} --role=roles/stackdriver.resourceMetadata.writer
```

### Build our GKE Cluster

```bash
gcloud container clusters create $CLUSTER_NAME \
  --location "$REGION" \
  --workload-pool "${PROJECT_ID}.svc.id.goog" \
  --enable-image-streaming --enable-shielded-nodes \
  --shielded-secure-boot --shielded-integrity-monitoring \
  --enable-ip-alias \
  --network=$NETWORK \
  --node-locations="$ZONE_1" \
  --workload-pool="${PROJECT_ID}.svc.id.goog" \
  --addons GcsFuseCsiDriver   \
  --no-enable-master-authorized-networks \
  --machine-type n2d-standard-4 \
  --num-nodes 1 --min-nodes 1 --max-nodes 5 \
  --ephemeral-storage-local-ssd=count=2 \
  --enable-ip-alias \
  --scopes="cloud-platform"
```

New nodepool

```bash
gcloud container node-pools create g2-standard-24 --cluster $CLUSTER_NAME \
  --accelerator type=nvidia-l4,count=2,gpu-driver-version=latest \
  --machine-type g2-standard-24 \
  --ephemeral-storage-local-ssd=count=2 \
  --enable-autoscaling --enable-image-streaming \
  --num-nodes=1 --min-nodes=0 --max-nodes=4 \
  --shielded-secure-boot \
  --shielded-integrity-monitoring \
  --node-locations $ZONE_1,$ZONE_2 --region $REGION
```


Check for GPUs 

```bash
kubectl get nodes -o json | jq -r '.items[] | {name:.metadata.name, gpus:.status.capacity."nvidia.com/gpu"}'
```


Test after running Docker Container Locally
```bash
curl -s 127.0.0.1:3000/generate -X POST -H 'Content-Type: application/json' — data-binary @- <<EOF | jq -r '.generated_text'
{
  "inputs": "[INST] <<SYS>>\nYou are a helpful, respectful and honest assistant. Always answer as helpfully as possible, while being safe. \
  Your answers should not include any harmful, unethical, racist, sexist, toxic, dangerous, or illegal content. Please ensure that \
  your responses are socially unbiased and positive in nature. If a question does not make any sense, or is not factually coherent, explain \
  why instead of answering something not correct. If you don’t know the answer to a question, please don’t share false \
  information.\n<</SYS>>\nHow to deploy a container on K8s?[/INST]",
  "parameters": {"max_new_tokens": 400}
}
EOF
```