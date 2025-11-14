import { useState } from 'react'
import { Card, Button, Space, Typography, Alert, Spin, Descriptions, Tag } from 'antd'
import {
  DeleteOutlined,
  ApiOutlined,
  InfoCircleOutlined,
  DollarOutlined,
  FileTextOutlined,
  ReloadOutlined
} from '@ant-design/icons'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { creditPortfolioApi } from '@/api/creditPortfolio'
import { useDepartment } from '@/contexts/DepartmentContext'

const { Title, Text, Paragraph } = Typography

interface TestResult {
  success?: boolean
  data?: any
  error?: string
  details?: any
}

export default function DebugPage() {
  const { selectedDepartment } = useDepartment()
  const queryClient = useQueryClient()
  const [result, setResult] = useState<TestResult | null>(null)
  const [loading, setLoading] = useState(false)
  const [activeTest, setActiveTest] = useState<string>('')

  // Clear all React Query cache
  const clearAllCache = () => {
    queryClient.clear()
    localStorage.clear()
    sessionStorage.clear()
    setResult({
      success: true,
      data: 'All cache cleared! (React Query + localStorage + sessionStorage)'
    })
    setActiveTest('clear-cache')
  }

  // Invalidate specific query
  const invalidateAnalytics = () => {
    queryClient.invalidateQueries({ queryKey: ['credit-portfolio'] })
    setResult({
      success: true,
      data: 'Credit portfolio queries invalidated'
    })
    setActiveTest('invalidate')
  }

  // Test summary API
  const testSummaryAPI = async () => {
    setLoading(true)
    setActiveTest('summary')
    try {
      const data = await creditPortfolioApi.getSummary({
        department_id: selectedDepartment?.id
      })
      setResult({
        success: true,
        data
      })
      console.log('Summary API response:', data)
    } catch (error: any) {
      setResult({
        success: false,
        error: error.message,
        details: error.response?.data
      })
      console.error('API Error:', error)
    } finally {
      setLoading(false)
    }
  }

  // Test organizations API
  const testOrganizationsAPI = async () => {
    setLoading(true)
    setActiveTest('organizations')
    try {
      const data = await creditPortfolioApi.getOrganizations({
        department_id: selectedDepartment?.id,
        limit: 5
      })
      setResult({
        success: true,
        data
      })
      console.log('Organizations API response:', data)
    } catch (error: any) {
      setResult({
        success: false,
        error: error.message,
        details: error.response?.data
      })
      console.error('API Error:', error)
    } finally {
      setLoading(false)
    }
  }

  // Test contracts API
  const testContractsAPI = async () => {
    setLoading(true)
    setActiveTest('contracts')
    try {
      const data = await creditPortfolioApi.getContracts({
        department_id: selectedDepartment?.id,
        limit: 5
      })
      setResult({
        success: true,
        data
      })
      console.log('Contracts API response:', data)
    } catch (error: any) {
      setResult({
        success: false,
        error: error.message,
        details: error.response?.data
      })
      console.error('API Error:', error)
    } finally {
      setLoading(false)
    }
  }

  // Test receipts API
  const testReceiptsAPI = async () => {
    setLoading(true)
    setActiveTest('receipts')
    try {
      const data = await creditPortfolioApi.getReceipts({
        department_id: selectedDepartment?.id,
        limit: 5
      })
      setResult({
        success: true,
        data
      })
      console.log('Receipts API response:', data)
    } catch (error: any) {
      setResult({
        success: false,
        error: error.message,
        details: error.response?.data
      })
      console.error('API Error:', error)
    } finally {
      setLoading(false)
    }
  }

  // Test expenses API
  const testExpensesAPI = async () => {
    setLoading(true)
    setActiveTest('expenses')
    try {
      const data = await creditPortfolioApi.getExpenses({
        department_id: selectedDepartment?.id,
        limit: 5
      })
      setResult({
        success: true,
        data
      })
      console.log('Expenses API response:', data)
    } catch (error: any) {
      setResult({
        success: false,
        error: error.message,
        details: error.response?.data
      })
      console.error('API Error:', error)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div style={{ padding: 24 }}>
      <Title level={2}>🔧 Debug Page</Title>
      <Paragraph type="secondary">
        Development tools for testing API endpoints, cache management, and debugging
      </Paragraph>

      {/* Environment Info */}
      <Card
        title={
          <Space>
            <InfoCircleOutlined />
            <span>Environment Information</span>
          </Space>
        }
        style={{ marginBottom: 24 }}
      >
        <Descriptions column={2} bordered size="small">
          <Descriptions.Item label="API URL">
            <Text code>{import.meta.env.VITE_API_URL || 'Not set'}</Text>
          </Descriptions.Item>
          <Descriptions.Item label="Environment">
            <Tag color={import.meta.env.DEV ? 'orange' : 'green'}>
              {import.meta.env.DEV ? 'Development' : 'Production'}
            </Tag>
          </Descriptions.Item>
          <Descriptions.Item label="Selected Department">
            <Text strong>{selectedDepartment?.name || 'None'}</Text>
          </Descriptions.Item>
          <Descriptions.Item label="Department ID">
            <Text code>{selectedDepartment?.id || 'N/A'}</Text>
          </Descriptions.Item>
          <Descriptions.Item label="React Query Cache">
            <Text>{queryClient.getQueryCache().getAll().length} queries</Text>
          </Descriptions.Item>
          <Descriptions.Item label="localStorage Size">
            <Text>{new Blob(Object.values(localStorage)).size} bytes</Text>
          </Descriptions.Item>
        </Descriptions>
      </Card>

      {/* Cache Management */}
      <Card
        title={
          <Space>
            <DeleteOutlined />
            <span>Cache Management</span>
          </Space>
        }
        style={{ marginBottom: 24 }}
      >
        <Space wrap>
          <Button
            type="primary"
            danger
            icon={<DeleteOutlined />}
            onClick={clearAllCache}
          >
            Clear All Cache
          </Button>
          <Button
            icon={<ReloadOutlined />}
            onClick={invalidateAnalytics}
          >
            Invalidate Analytics Cache
          </Button>
        </Space>
      </Card>

      {/* API Testing */}
      <Card
        title={
          <Space>
            <ApiOutlined />
            <span>API Testing</span>
          </Space>
        }
        style={{ marginBottom: 24 }}
      >
        <Space wrap>
          <Button
            icon={<DollarOutlined />}
            onClick={testSummaryAPI}
            loading={loading && activeTest === 'summary'}
            disabled={loading && activeTest !== 'summary'}
          >
            Test Summary API
          </Button>
          <Button
            icon={<FileTextOutlined />}
            onClick={testOrganizationsAPI}
            loading={loading && activeTest === 'organizations'}
            disabled={loading && activeTest !== 'organizations'}
          >
            Test Organizations
          </Button>
          <Button
            icon={<FileTextOutlined />}
            onClick={testContractsAPI}
            loading={loading && activeTest === 'contracts'}
            disabled={loading && activeTest !== 'contracts'}
          >
            Test Contracts
          </Button>
          <Button
            icon={<DollarOutlined />}
            onClick={testReceiptsAPI}
            loading={loading && activeTest === 'receipts'}
            disabled={loading && activeTest !== 'receipts'}
          >
            Test Receipts
          </Button>
          <Button
            icon={<DollarOutlined />}
            onClick={testExpensesAPI}
            loading={loading && activeTest === 'expenses'}
            disabled={loading && activeTest !== 'expenses'}
          >
            Test Expenses
          </Button>
        </Space>
      </Card>

      {/* Loading Indicator */}
      {loading && (
        <Card style={{ marginBottom: 24 }}>
          <div style={{ textAlign: 'center', padding: '20px 0' }}>
            <Spin size="large" />
            <Paragraph style={{ marginTop: 16 }}>Loading...</Paragraph>
          </div>
        </Card>
      )}

      {/* Results */}
      {result && !loading && (
        <Card
          title={
            result.success ? (
              <Text type="success">✅ Success</Text>
            ) : (
              <Text type="danger">❌ Error</Text>
            )
          }
        >
          {result.error && (
            <Alert
              message="Error"
              description={result.error}
              type="error"
              showIcon
              style={{ marginBottom: 16 }}
            />
          )}

          <div
            style={{
              backgroundColor: '#f5f5f5',
              padding: 16,
              borderRadius: 4,
              overflow: 'auto',
              maxHeight: 500
            }}
          >
            <pre style={{ margin: 0, fontSize: 12, fontFamily: 'monospace' }}>
              {JSON.stringify(result.data || result.details, null, 2)}
            </pre>
          </div>
        </Card>
      )}
    </div>
  )
}
