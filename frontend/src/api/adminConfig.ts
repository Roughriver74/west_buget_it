import apiClient from './client'

export interface AdminConfig {
  app_name: string
  odata_url: string
  odata_username: string
  odata_password: string
  odata_custom_auth_token: string
  vsegpt_api_key: string | null
  vsegpt_base_url: string
  vsegpt_model: string
  credit_portfolio_ftp_host: string
  credit_portfolio_ftp_user: string
  credit_portfolio_ftp_password: string
  credit_portfolio_ftp_remote_dir: string
  credit_portfolio_ftp_local_dir: string
  scheduler_enabled: boolean
  credit_portfolio_import_enabled: boolean
  credit_portfolio_import_hour: number
  credit_portfolio_import_minute: number
}

export const adminConfigApi = {
  get: async (): Promise<AdminConfig> => {
    const { data } = await apiClient.get('admin/config')
    return data
  },

  update: async (payload: Partial<AdminConfig>): Promise<AdminConfig> => {
    const { data } = await apiClient.put('admin/config', payload)
    return data
  },
}
