# Terraform - AWS VPC + EKS for StockPilot

Creates, in `ap-south-1` by default:

```text
VPC 10.20.0.0/16
 ├── 2 public subnets  (tagged kubernetes.io/role/elb)       -> internet-facing load balancers
 ├── 2 private subnets (tagged kubernetes.io/role/internal-elb) -> worker nodes
 ├── Internet gateway + 1 NAT gateway
 └── EKS cluster (Kubernetes 1.31)
       ├── managed node group: 2 x t3.medium
       └── add-ons: coredns, kube-proxy, vpc-cni, aws-ebs-csi-driver (IRSA role)
```

> **Cost:** EKS control plane + 2 × t3.medium + NAT gateway ≈ US$0.25/hour (~US$6/day).
> Run `terraform destroy` as soon as you have your screenshots.

## Prerequisites

* Terraform ≥ 1.7, AWS CLI v2, kubectl, Helm
* `aws configure` with an IAM user/role allowed to create VPC, EKS, IAM and EC2 resources.
  **Never** commit keys — Terraform reads them from your AWS CLI profile.

## Run

```bash
cd terraform
cp terraform.tfvars.example terraform.tfvars   # optional overrides
terraform init
terraform fmt -check
terraform validate
terraform plan -out tfplan          # screenshot this
terraform apply tfplan              # ~15 minutes
$(terraform output -raw configure_kubectl)
kubectl get nodes
```

Then follow **Part I – Deploy to EKS** in the root README.

## Tear down

```bash
# remove Kubernetes-created load balancers first so the VPC can be deleted
helm uninstall stockpilot -n stockpilot
helm uninstall ingress-nginx -n ingress-nginx
terraform destroy                   # screenshot the "Destroy complete!" line
```
