"""A Google Cloud Python Pulumi program"""

import pulumi
import pulumi_gcp as gcp

# Read in some configurable settings for our cluster.
# If nothing is set the specified default values will take effect.
config = pulumi.Config()
NODE_COUNT = config.get_int('node_count') or 1
NODE_MACHINE_TYPE = config.get('node_machine_type') or 'n2d-standard-4'
MASTER_VERSION = config.get('master_version') or '1.27.8-gke.1067004'
CLUSTER_NAME = config.get('cluster_name') or 'llm-serving-cluster'
PROJECT_ID = config.get('project_id')
REGION =  config.get('region') or "us-central1"
GKE_NETWORK = config.get("gke_network") or "default"

# Defining the GKE Cluster
gke_cluster = gcp.container.Cluster('cluster-1', 
    name = CLUSTER_NAME,
    location = REGION,
    initial_node_count = NODE_COUNT,
    remove_default_node_pool = True,
    enable_shielded_nodes = True,
    min_master_version = MASTER_VERSION,
    network = GKE_NETWORK,
    workload_identity_config={"identity_namespace": f"{PROJECT_ID}.svc.id.goog"},
    ip_allocation_policy=gcp.container.ClusterIpAllocationPolicyArgs(
        use_ip_aliases=True
    ),
)

# Defining the GKE Node Pool
gke_nodepool = gcp.container.NodePool("nodepool-1",
    name = "nodepool-1",
    location = "us-central1",
    node_locations = ["us-central1-a"],
    cluster = gke_cluster.id,
    node_count = NODE_COUNT,
    node_config = gcp.container.NodePoolNodeConfigArgs(
        preemptible = False,
        machine_type = NODE_MACHINE_TYPE,
        disk_size_gb = 20,
        oauth_scopes = ["https://www.googleapis.com/auth/cloud-platform"],
        shielded_instance_config = gcp.container.NodePoolNodeConfigShieldedInstanceConfigArgs(
            enable_integrity_monitoring = True,
            enable_secure_boot = True
        )
    ),
    # Set the Nodepool Autoscaling configuration
    autoscaling = gcp.container.NodePoolAutoscalingArgs(
        min_node_count = 1,
        max_node_count = 3
    ),
    # Set the Nodepool Management configuration
    management = gcp.container.NodePoolManagementArgs(
        auto_repair  = True,
        auto_upgrade = True
    )
)
