terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

# Cloud SQL - PostgreSQL
resource "google_sql_database_instance" "main" {
  name             = "afrianalyze-db"
  database_version = "POSTGRES_15"
  region           = var.region

  settings {
    tier = "db-f1-micro" # Use appropriate tier for prod
  }
  deletion_protection = false # Set to true for real prod
}

resource "google_sql_database" "database" {
  name     = "afrianalyzedb"
  instance = google_sql_database_instance.main.name
}

resource "google_sql_user" "users" {
  name     = "afri_user"
  instance = google_sql_database_instance.main.name
  password = var.db_password
}

# Memorystore - Redis
resource "google_redis_instance" "cache" {
  name           = "afrianalyze-cache"
  memory_size_gb = 1
  region         = var.region
  redis_version  = "REDIS_6_X"
}

# Secret Manager
resource "google_secret_manager_secret" "api_secret" {
  secret_id = "api-secret"

  replication {
    auto {}
  }
}

# Cloud Run - Backend (API)
resource "google_cloud_run_v2_service" "api" {
  name     = "afrianalyze-api"
  location = var.region
  
  template {
    containers {
      image = "gcr.io/${var.project_id}/afrianalyze-api:latest"
      
      env {
        name  = "DATABASE_URL"
        value = "postgresql://afri_user:${var.db_password}@${google_sql_database_instance.main.public_ip_address}/afrianalyzedb"
      }
      env {
        name  = "REDIS_URL"
        value = "redis://${google_redis_instance.cache.host}:${google_redis_instance.cache.port}"
      }
    }
  }
}

# Cloud Run - Frontend (Web)
resource "google_cloud_run_v2_service" "web" {
  name     = "afrianalyze-web"
  location = var.region
  
  template {
    containers {
      image = "gcr.io/${var.project_id}/afrianalyze-web:latest"
      
      env {
        name  = "NEXT_PUBLIC_API_URL"
        value = google_cloud_run_v2_service.api.uri
      }
    }
  }
}
