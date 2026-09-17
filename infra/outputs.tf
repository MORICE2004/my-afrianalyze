output "api_url" {
  description = "The URL of the API Cloud Run service"
  value       = google_cloud_run_v2_service.api.uri
}

output "web_url" {
  description = "The URL of the Web Cloud Run service"
  value       = google_cloud_run_v2_service.web.uri
}

output "database_instance_ip" {
  description = "The IP address of the Cloud SQL instance"
  value       = google_sql_database_instance.main.public_ip_address
}

output "redis_host" {
  description = "The host of the Memorystore Redis instance"
  value       = google_redis_instance.cache.host
}
