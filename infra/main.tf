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

variable "project_id" {
  type = string
}

variable "region" {
  type    = string
  default = "europe-west1"
}

# Secret Manager
resource "google_secret_manager_secret" "db_password" {
  secret_id = "db-password"
  replication {
    auto {}
  }
}

resource "google_secret_manager_secret_version" "db_password_version" {
  secret      = google_secret_manager_secret.db_password.id
  secret_data = var.db_password
}

variable "db_password" {
  type      = string
  sensitive = true
}

# Cloud SQL PostgreSQL
resource "google_sql_database_instance" "main" {
  name             = "afrianalyze-db-instance"
  database_version = "POSTGRES_15"
  region           = var.region

  settings {
    tier = "db-f1-micro"
  }
  deletion_protection = false
}

resource "google_sql_database" "database" {
  name     = "afrianalyze"
  instance = google_sql_database_instance.main.name
}

resource "google_sql_user" "users" {
  name     = "afrianalyze"
  instance = google_sql_database_instance.main.name
  password = google_secret_manager_secret_version.db_password_version.secret_data
}

# Cloud Run (API)
resource "google_cloud_run_v2_service" "api" {
  name     = "afrianalyze-api"
  location = var.region

  template {
    containers {
      image = "gcr.io/${var.project_id}/afrianalyze-api:latest"
      env {
        name  = "DATABASE_URL"
        value = "postgresql://afrianalyze:${google_secret_manager_secret_version.db_password_version.secret_data}@/afrianalyze?host=/cloudsql/${google_sql_database_instance.main.connection_name}"
      }
      env {
        name  = "ENVIRONMENT"
        value = "production"
      }
    }
    volumes {
      name = "cloudsql"
      cloud_sql_instance {
        instances = [google_sql_database_instance.main.connection_name]
      }
    }
  }
}

# Cloud Run (Web)
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

# IAM for Cloud Run to access Secret Manager and Cloud SQL
resource "google_project_iam_member" "cloud_run_sql" {
  project = var.project_id
  role    = "roles/cloudsql.client"
  member  = "serviceAccount:${google_cloud_run_v2_service.api.template[0].service_account}"
}

resource "google_project_iam_member" "cloud_run_secret" {
  project = var.project_id
  role    = "roles/secretmanager.secretAccessor"
  member  = "serviceAccount:${google_cloud_run_v2_service.api.template[0].service_account}"
}
