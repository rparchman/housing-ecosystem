#!/usr/bin/env bash
set -e

echo "Bootstrapping Helm + GitHub Actions + K8s infra..."

# Helm chart structure
mkdir -p helm/housing-ecosystem/templates

cat > helm/housing-ecosystem/Chart.yaml <<'EOF'
apiVersion: v2
name: housing-ecosystem
description: Michigan Housing Ecosystem (API + Scheduler)
type: application
version: 0.1.0
appVersion: "1.0.0"
EOF

cat > helm/housing-ecosystem/values.yaml <<'EOF'
# Default (dev) values
global:
  appName: housing-ecosystem

api:
  image: your-registry/housing-api:latest
  replicas: 1
  resources:
    requests:
      cpu: "250m"
      memory: "256Mi"
    limits:
      cpu: "500m"
      memory: "512Mi"

scheduler:
  image: your-registry/gis-scheduler:latest
  replicas: 1
  resources:
    requests:
      cpu: "100m"
      memory: "128Mi"
    limits:
      cpu: "250m"
      memory: "256Mi"

ingress:
  enabled: true
  host: dev.housing.yourdomain.com

config:
  LOG_LEVEL: "info"

secrets:
  SLACK_WEBHOOK: ""
  EMAIL_SENDER: ""
  EMAIL_PASSWORD: ""
  EMAIL_RECIPIENT: ""
EOF

cat > helm/housing-ecosystem/values-prod.yaml <<'EOF'
global:
  appName: housing-ecosystem

api:
  image: your-registry/housing-api:prod
  replicas: 3
  resources:
    requests:
      cpu: "500m"
      memory: "512Mi"
    limits:
      cpu: "1"
      memory: "1Gi"

scheduler:
  image: your-registry/gis-scheduler:prod
  replicas: 1
  resources:
    requests:
      cpu: "250m"
      memory: "256Mi"
    limits:
      cpu: "500m"
      memory: "512Mi"

ingress:
  enabled: true
  host: housing.yourdomain.com

config:
  LOG_LEVEL: "warn"

secrets:
  SLACK_WEBHOOK: ""
  EMAIL_SENDER: ""
  EMAIL_PASSWORD: ""
  EMAIL_RECIPIENT: ""
EOF

cat > helm/housing-ecosystem/values-staging.yaml <<'EOF'
global:
  appName: housing-ecosystem

api:
  image: your-registry/housing-api:staging
  replicas: 2
  resources:
    requests:
      cpu: "250m"
      memory: "256Mi"
    limits:
      cpu: "750m"
      memory: "768Mi"

scheduler:
  image: your-registry/gis-scheduler:staging
  replicas: 1
  resources:
    requests:
      cpu: "150m"
      memory: "192Mi"
    limits:
      cpu: "300m"
      memory: "384Mi"

ingress:
  enabled: true
  host: staging.housing.yourdomain.com

config:
  LOG_LEVEL: "debug"

secrets:
  SLACK_WEBHOOK: ""
  EMAIL_SENDER: ""
  EMAIL_PASSWORD: ""
  EMAIL_RECIPIENT: ""
EOF

cat > helm/housing-ecosystem/templates/_helpers.tpl <<'EOF'
{{- define "housing-ecosystem.apiName" -}}
{{ .Values.global.appName }}-api
{{- end }}

{{- define "housing-ecosystem.schedulerName" -}}
{{ .Values.global.appName }}-scheduler
{{- end }}

{{- define "housing-ecosystem.apiServiceName" -}}
{{ .Values.global.appName }}-api-service
{{- end }}
EOF

cat > helm/housing-ecosystem/templates/api-deployment.yaml <<'EOF'
apiVersion: apps/v1
kind: Deployment
metadata:
  name: {{ include "housing-ecosystem.apiName" . }}
  labels:
    app: {{ include "housing-ecosystem.apiName" . }}
spec:
  replicas: {{ .Values.api.replicas }}
  selector:
    matchLabels:
      app: {{ include "housing-ecosystem.apiName" . }}
  template:
    metadata:
      labels:
        app: {{ include "housing-ecosystem.apiName" . }}
    spec:
      containers:
        - name: api
          image: {{ .Values.api.image }}
          ports:
            - containerPort: 80
          envFrom:
            - configMapRef:
                name: {{ include "housing-ecosystem.apiName" . }}-config
            - secretRef:
                name: {{ include "housing-ecosystem.apiName" . }}-secrets
          resources:
            requests:
              cpu: {{ .Values.api.resources.requests.cpu }}
              memory: {{ .Values.api.resources.requests.memory }}
            limits:
              cpu: {{ .Values.api.resources.limits.cpu }}
              memory: {{ .Values.api.resources.limits.memory }}
EOF

cat > helm/housing-ecosystem/templates/api-service.yaml <<'EOF'
apiVersion: v1
kind: Service
metadata:
  name: {{ include "housing-ecosystem.apiServiceName" . }}
spec:
  type: ClusterIP
  selector:
    app: {{ include "housing-ecosystem.apiName" . }}
  ports:
    - port: 80
      targetPort: 80
      protocol: TCP
EOF

cat > helm/housing-ecosystem/templates/scheduler-deployment.yaml <<'EOF'
apiVersion: apps/v1
kind: Deployment
metadata:
  name: {{ include "housing-ecosystem.schedulerName" . }}
  labels:
    app: {{ include "housing-ecosystem.schedulerName" . }}
spec:
  replicas: {{ .Values.scheduler.replicas }}
  selector:
    matchLabels:
      app: {{ include "housing-ecosystem.schedulerName" . }}
  template:
    metadata:
      labels:
        app: {{ include "housing-ecosystem.schedulerName" . }}
    spec:
      containers:
        - name: scheduler
          image: {{ .Values.scheduler.image }}
          envFrom:
            - configMapRef:
                name: {{ include "housing-ecosystem.schedulerName" . }}-config
            - secretRef:
                name: {{ include "housing-ecosystem.schedulerName" . }}-secrets
          resources:
            requests:
              cpu: {{ .Values.scheduler.resources.requests.cpu }}
              memory: {{ .Values.scheduler.resources.requests.memory }}
            limits:
              cpu: {{ .Values.scheduler.resources.limits.cpu }}
              memory: {{ .Values.scheduler.resources.limits.memory }}
EOF

cat > helm/housing-ecosystem/templates/ingress.yaml <<'EOF'
{{- if .Values.ingress.enabled }}
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: {{ .Values.global.appName }}-ingress
  annotations:
    kubernetes.io/ingress.class: nginx
spec:
  rules:
    - host: {{ .Values.ingress.host }}
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: {{ include "housing-ecosystem.apiServiceName" . }}
                port:
                  number: 80
{{- end }}
EOF

cat > helm/housing-ecosystem/templates/configmap.yaml <<'EOF'
apiVersion: v1
kind: ConfigMap
metadata:
  name: {{ include "housing-ecosystem.apiName" . }}-config
data:
  LOG_LEVEL: {{ .Values.config.LOG_LEVEL | quote }}

---
apiVersion: v1
kind: ConfigMap
metadata:
  name: {{ include "housing-ecosystem.schedulerName" . }}-config
data:
  LOG_LEVEL: {{ .Values.config.LOG_LEVEL | quote }}
EOF

cat > helm/housing-ecosystem/templates/secrets.yaml <<'EOF'
apiVersion: v1
kind: Secret
metadata:
  name: {{ include "housing-ecosystem.apiName" . }}-secrets
type: Opaque
stringData:
  SLACK_WEBHOOK: {{ .Values.secrets.SLACK_WEBHOOK | quote }}
  EMAIL_SENDER: {{ .Values.secrets.EMAIL_SENDER | quote }}
  EMAIL_PASSWORD: {{ .Values.secrets.EMAIL_PASSWORD | quote }}
  EMAIL_RECIPIENT: {{ .Values.secrets.EMAIL_RECIPIENT | quote }}

---
apiVersion: v1
kind: Secret
metadata:
  name: {{ include "housing-ecosystem.schedulerName" . }}-secrets
type: Opaque
stringData:
  SLACK_WEBHOOK: {{ .Values.secrets.SLACK_WEBHOOK | quote }}
  EMAIL_SENDER: {{ .Values.secrets.EMAIL_SENDER | quote }}
  EMAIL_PASSWORD: {{ .Values.secrets.EMAIL_PASSWORD | quote }}
  EMAIL_RECIPIENT: {{ .Values.secrets.EMAIL_RECIPIENT | quote }}
EOF

# GitHub Actions workflow
mkdir -p .github/workflows

cat > .github/workflows/cicd-housing-ecosystem.yml <<'EOF'
name: CI/CD - Housing Ecosystem

on:
  push:
    branches: [ main ]
  workflow_dispatch:
    inputs:
      environment:
        description: "Environment (dev|staging|prod)"
        required: true
        default: "dev"
      region:
        description: "Region (us-east-1|us-west-2|eu-central-1)"
        required: true
        default: "us-east-1"

jobs:
  build-and-push:
    runs-on: ubuntu-latest
    env:
      REGISTRY: your-registry
    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3

      - name: Login to registry
        uses: docker/login-action@v3
        with:
          registry: ${{ env.REGISTRY }}
          username: ${{ secrets.REGISTRY_USERNAME }}
          password: ${{ secrets.REGISTRY_PASSWORD }}

      - name: Build and push API image
        uses: docker/build-push-action@v5
        with:
          context: .
          file: deployment/api/Dockerfile
          push: true
          tags: |
            ${{ env.REGISTRY }}/housing-api:${{ github.sha }}

      - name: Build and push Scheduler image
        uses: docker/build-push-action@v5
        with:
          context: .
          file: deployment/scheduler/Dockerfile
          push: true
          tags: |
            ${{ env.REGISTRY }}/gis-scheduler:${{ github.sha }}

  deploy:
    needs: build-and-push
    runs-on: ubuntu-latest
    env:
      KUBE_CONFIG: ${{ secrets.KUBE_CONFIG }}
    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Set up kubectl
        uses: azure/setup-kubectl@v4
        with:
          version: "latest"

      - name: Configure kubeconfig
        run: |
          mkdir -p ~/.kube
          echo "${KUBE_CONFIG}" > ~/.kube/config

      - name: Set environment values file
        id: envfile
        run: |
          ENV="${{ github.event.inputs.environment || 'dev' }}"
          if [ "$ENV" = "prod" ]; then
            echo "file=helm/housing-ecosystem/values-prod.yaml" >> $GITHUB_OUTPUT
          elif [ "$ENV" = "staging" ]; then
            echo "file=helm/housing-ecosystem/values-staging.yaml" >> $GITHUB_OUTPUT
          else
            echo "file=helm/housing-ecosystem/values.yaml" >> $GITHUB_OUTPUT
          fi

      - name: Install Helm
        uses: azure/setup-helm@v4
        with:
          version: "v3.14.0"

      - name: Helm upgrade (multi-region)
        run: |
          REGION="${{ github.event.inputs.region || 'us-east-1' }}"
          RELEASE="housing-ecosystem-${REGION}"
          helm upgrade --install "$RELEASE" helm/housing-ecosystem \
            -f ${{ steps.envfile.outputs.file }} \
            --set api.image=${{ env.REGISTRY }}/housing-api:${{ github.sha }} \
            --set scheduler.image=${{ env.REGISTRY }}/gis-scheduler:${{ github.sha }} \
            --namespace housing-${REGION} \
            --create-namespace
EOF

echo "Done. Helm + CI/CD + K8s infra scaffolded."
