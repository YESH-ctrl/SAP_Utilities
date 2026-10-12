export interface HealthServiceStatus {
  status: 'healthy' | 'degraded' | 'down';
  latency_ms?: number;
  message?: string;
  details?: Record<string, any>;
}

export interface SystemHealthResponse {
  status: 'healthy' | 'degraded' | 'down';
  version: string;
  environment: string;
  uptime_seconds?: number;
  timestamp: string;
  services: {
    api: HealthServiceStatus;
    database: HealthServiceStatus;
    pgvector: HealthServiceStatus;
    embedding: HealthServiceStatus;
    llm: HealthServiceStatus;
  };
}
