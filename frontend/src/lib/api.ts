const API_URL = import.meta.env.VITE_API_URL ?? 'http://localhost:8000'

export interface HealthStatus {
  status: string
}

export async function getHealth(): Promise<HealthStatus> {
  const response = await fetch(`${API_URL}/api/health`)
  if (!response.ok) {
    throw new Error(`Backend health check failed: ${response.status}`)
  }
  return response.json()
}
