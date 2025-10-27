/**
 * Budget Planning Page
 * Main page for budget planning module with scenarios and versions
 */
import React, { useMemo, useState } from 'react'
import {
  Typography,
  Row,
  Col,
  Button,
  Space,
  Card,
  Select,
  Empty,
  Modal,
  Form,
  Input,
  InputNumber,
  Result,
} from 'antd'
import { PlusOutlined, CalculatorOutlined } from '@ant-design/icons'
import { useDepartment } from '@/contexts/DepartmentContext'
import { useAuth } from '@/contexts/AuthContext'
import { useQuery } from '@tanstack/react-query'
import { categoriesApi } from '@/api/categories'
import { BudgetScenarioCard } from '@/components/budget/BudgetScenarioCard'
import { BudgetVersionTable } from '@/components/budget/BudgetVersionTable'
import { BudgetCalculatorForm } from '@/components/budget/BudgetCalculatorForm'
import { BudgetVersionDetailDrawer } from '@/components/budget/BudgetVersionDetailDrawer'
import {
  useBudgetScenarios,
  useBudgetVersions,
  useCreateScenario,
  useCreateVersion,
  useDeleteScenario,
  useDeleteVersion,
  useSubmitVersion,
} from '@/hooks/useBudgetPlanning'
import { BudgetScenarioType } from '@/types/budgetPlanning'
import type { BudgetScenario } from '@/types/budgetPlanning'
import LoadingState from '@/components/common/LoadingState'
import ErrorState from '@/components/common/ErrorState'

const { Title, Text } = Typography

const BudgetPlanningPage: React.FC = () => {
  const { selectedDepartment } = useDepartment()
  const { user } = useAuth()
  const [selectedYear, setSelectedYear] = useState(new Date().getFullYear() + 1)
  const [selectedScenario, setSelectedScenario] = useState<BudgetScenario | null>(null)
  const [isScenarioModalOpen, setIsScenarioModalOpen] = useState(false)
  const [isVersionModalOpen, setIsVersionModalOpen] = useState(false)
  const [isCalculatorOpen, setIsCalculatorOpen] = useState(false)
  const [isVersionDetailOpen, setIsVersionDetailOpen] = useState(false)
  const [versionDetailMode, setVersionDetailMode] = useState<'view' | 'edit'>('view')
  const [activeVersionId, setActiveVersionId] = useState<number | null>(null)
  const [scenarioForm] = Form.useForm()
  const [versionForm] = Form.useForm()

  const departmentId = selectedDepartment?.id ?? (user?.department_id ?? undefined)

  // Queries
  const {
    data: scenarios = [],
    isLoading: scenariosLoading,
    isError: scenariosError,
    error: scenariosErrorObj,
    refetch: refetchScenarios,
  } = useBudgetScenarios({
    year: selectedYear,
  })

  const {
    data: versions = [],
    isLoading: versionsLoading,
    refetch: refetchVersions,
    isError: versionsError,
    error: versionsErrorObj,
  } = useBudgetVersions({
    year: selectedYear,
    scenario_id: selectedScenario?.id,
  })

  const {
    data: categories = [],
    isLoading: categoriesLoading,
    isError: categoriesError,
    error: categoriesErrorObj,
    refetch: refetchCategories,
  } = useQuery({
    queryKey: ['categories', { department_id: departmentId, is_active: true }],
    queryFn: () =>
      categoriesApi.getAll({
        is_active: true,
        ...(departmentId ? { department_id: departmentId } : {}),
      }),
  })

  const categoryOptions = useMemo(
    () =>
      categories.map((cat) => ({
        id: cat.id,
        name: cat.name,
        type: cat.type,
        parentId: cat.parent_id ?? null,
      })),
    [categories]
  )

  // Mutations
  const createScenario = useCreateScenario()
  const deleteScenario = useDeleteScenario()
  const createVersion = useCreateVersion()
  const deleteVersion = useDeleteVersion()
  const submitVersion = useSubmitVersion()

  // Handlers
  const handleCreateScenario = async () => {
    try {
      const values = await scenarioForm.validateFields()
      await createScenario.mutateAsync({
        year: selectedYear,
        scenario_name: values.scenario_name,
        scenario_type: values.scenario_type,
        global_growth_rate: values.global_growth_rate || 0,
        inflation_rate: values.inflation_rate || 0,
        fx_rate: values.fx_rate,
        description: values.description,
      })
      scenarioForm.resetFields()
      setIsScenarioModalOpen(false)
    } catch (error) {
      console.error('Error creating scenario:', error)
    }
  }

  const handleDeleteScenario = async (id: number) => {
    await deleteScenario.mutateAsync(id)
    if (selectedScenario?.id === id) {
      setSelectedScenario(null)
    }
  }

  const handleCreateVersion = async () => {
    try {
      const values = await versionForm.validateFields()
      await createVersion.mutateAsync({
        year: selectedYear,
        version_name: values.version_name,
        scenario_id: selectedScenario?.id,
      })
      versionForm.resetFields()
      setIsVersionModalOpen(false)
    } catch (error) {
      console.error('Error creating version:', error)
    }
  }

  const handleDeleteVersion = async (id: number) => {
    await deleteVersion.mutateAsync(id)
  }

  const handleSubmitVersion = async (id: number) => {
    await submitVersion.mutateAsync(id)
  }

  const openVersionDrawer = (versionId: number, mode: 'view' | 'edit') => {
    setActiveVersionId(versionId)
    setVersionDetailMode(mode)
    setIsVersionDetailOpen(true)
  }

  const handleCopyVersion = (version: any) => {
    versionForm.setFieldsValue({
      version_name: `${version.version_name || 'Версия'} (копия)`,
      copy_from_version_id: version.id,
    })
    setIsVersionModalOpen(true)
  }

  const handleViewVersion = (version: any) => {
    openVersionDrawer(version.id, 'view')
  }

  const handleEditVersion = (version: any) => {
    openVersionDrawer(version.id, 'edit')
  }

  const handleVersionDrawerClose = () => {
    setIsVersionDetailOpen(false)
    setActiveVersionId(null)
  }

  // Generate year options (current year - 2 to current year + 5)
  const currentYear = new Date().getFullYear()
  const yearOptions = Array.from({ length: 8 }, (_, i) => currentYear - 2 + i)

  if (!departmentId) {
    return (
      <Result
        status="info"
        title="Выберите отдел"
        subTitle="Для планирования бюджета сначала выберите отдел в шапке приложения."
      />
    )
  }

  const getErrorMessage = (error: unknown) => (error instanceof Error ? error.message : 'Неизвестная ошибка')

  return (
    <div style={{ padding: '24px' }}>
      {/* Header */}
      <div style={{ marginBottom: 24 }}>
        <Title level={2}>Планирование бюджета</Title>
        <Text type="secondary">
          Создание сценариев и версий бюджета с автоматическим расчетом
        </Text>
      </div>

      {/* Year Selector */}
      <Card style={{ marginBottom: 24 }}>
        <Space>
          <Text strong>Год планирования:</Text>
          <Select
            value={selectedYear}
            onChange={setSelectedYear}
            style={{ width: 120 }}
          >
            {yearOptions.map((year) => (
              <Select.Option key={year} value={year}>
                {year}
              </Select.Option>
            ))}
          </Select>
        </Space>
      </Card>

      {/* Scenarios Section */}
      <Card
        title="Сценарии бюджета"
        extra={
          <Button
            type="primary"
            icon={<PlusOutlined />}
            onClick={() => setIsScenarioModalOpen(true)}
          >
            Создать сценарий
          </Button>
        }
        style={{ marginBottom: 24 }}
      >
        {scenariosLoading ? (
          <LoadingState fullHeight={false} message="Загрузка сценариев..." />
        ) : scenariosError ? (
          <ErrorState
            fullHeight={false}
            title="Не удалось загрузить сценарии"
            description={getErrorMessage(scenariosErrorObj)}
            onRetry={() => refetchScenarios()}
          />
        ) : scenarios.length === 0 ? (
          <Empty
            description={`Нет сценариев для ${selectedYear} года`}
            style={{ padding: 40 }}
          >
            <Button type="primary" onClick={() => setIsScenarioModalOpen(true)}>
              Создать первый сценарий
            </Button>
          </Empty>
        ) : (
          <Row gutter={[16, 16]}>
            {scenarios.map((scenario) => (
              <Col xs={24} lg={12} xxl={8} key={scenario.id}>
                <BudgetScenarioCard
                  scenario={scenario}
                  onDelete={handleDeleteScenario}
                  onSelect={setSelectedScenario}
                  selected={selectedScenario?.id === scenario.id}
                />
              </Col>
            ))}
          </Row>
        )}
      </Card>

      {/* Versions Section */}
      <Card
        title={
          selectedScenario
            ? `Версии бюджета: ${selectedScenario.scenario_name}`
            : 'Версии бюджета'
        }
        extra={
          <Space>
            <Button
              icon={<CalculatorOutlined />}
              onClick={() => setIsCalculatorOpen(true)}
              disabled={!selectedScenario || categoriesLoading || categoriesError}
            >
              Калькулятор
            </Button>
            <Button
              type="primary"
              icon={<PlusOutlined />}
              onClick={() => setIsVersionModalOpen(true)}
              disabled={!selectedScenario}
            >
              Создать версию
            </Button>
          </Space>
        }
      >
        {!selectedScenario ? (
          <Empty
            description="Выберите сценарий для просмотра версий"
            style={{ padding: 40 }}
          />
        ) : versionsLoading ? (
          <LoadingState fullHeight={false} message="Загрузка версий бюджета..." />
        ) : versionsError ? (
          <ErrorState
            fullHeight={false}
            title="Не удалось загрузить версии бюджета"
            description={getErrorMessage(versionsErrorObj)}
            onRetry={() => refetchVersions()}
          />
        ) : (
          <BudgetVersionTable
            versions={versions}
            loading={versionsLoading}
            onView={handleViewVersion}
            onEdit={handleEditVersion}
            onDelete={handleDeleteVersion}
            onSubmit={handleSubmitVersion}
            onCopy={handleCopyVersion}
          />
        )}
      </Card>

      {/* Create Scenario Modal */}
      <Modal
        title="Создать сценарий бюджета"
        open={isScenarioModalOpen}
        onCancel={() => {
          setIsScenarioModalOpen(false)
          scenarioForm.resetFields()
        }}
        onOk={handleCreateScenario}
        confirmLoading={createScenario.isPending}
      >
        <Form form={scenarioForm} layout="vertical">
          <Form.Item
            name="scenario_type"
            label="Тип сценария"
            rules={[{ required: true, message: 'Выберите тип сценария' }]}
          >
            <Select placeholder="Выберите тип">
              <Select.Option value={BudgetScenarioType.BASE}>Базовый</Select.Option>
              <Select.Option value={BudgetScenarioType.OPTIMISTIC}>Оптимистичный</Select.Option>
              <Select.Option value={BudgetScenarioType.PESSIMISTIC}>Пессимистичный</Select.Option>
            </Select>
          </Form.Item>

          <Form.Item
            name="scenario_name"
            label="Название"
            rules={[{ required: true, message: 'Введите название' }]}
          >
            <Input placeholder={`Базовый сценарий ${selectedYear}`} />
          </Form.Item>

          <Form.Item name="description" label="Описание">
            <Input.TextArea rows={3} placeholder="Описание сценария..." />
          </Form.Item>

          <Form.Item
            name="global_growth_rate"
            label="Глобальный процент роста (%)"
            tooltip="Общий ожидаемый рост расходов"
          >
            <InputNumber style={{ width: '100%' }} min={-50} max={100} />
          </Form.Item>

          <Form.Item
            name="inflation_rate"
            label="Инфляция (%)"
            tooltip="Ожидаемый уровень инфляции"
          >
            <InputNumber style={{ width: '100%' }} min={0} max={50} />
          </Form.Item>

          <Form.Item
            name="fx_rate"
            label="Курс валюты"
            tooltip="Прогнозный курс валюты (опционально)"
          >
            <InputNumber style={{ width: '100%' }} min={0} step={0.01} />
          </Form.Item>
        </Form>
      </Modal>

      {/* Create Version Modal */}
      <Modal
        title="Создать версию бюджета"
        open={isVersionModalOpen}
        onCancel={() => {
          setIsVersionModalOpen(false)
          versionForm.resetFields()
        }}
        onOk={handleCreateVersion}
        confirmLoading={createVersion.isPending}
      >
        <Form form={versionForm} layout="vertical">
          <Form.Item
            name="version_name"
            label="Название версии"
            tooltip="Опционально, будет сгенерировано автоматически"
          >
            <Input placeholder="Версия 1" />
          </Form.Item>

          <Form.Item name="copy_from_version_id" label="Копировать из версии" hidden>
            <InputNumber />
          </Form.Item>
        </Form>
      </Modal>

      {/* Budget Calculator Modal */}
      <BudgetCalculatorForm
        open={isCalculatorOpen}
        onClose={() => setIsCalculatorOpen(false)}
        categories={categories}
        defaultYear={selectedYear}
        departmentId={departmentId || 0}
      />

      {categoriesError && (
        <Card style={{ marginTop: 24 }} bodyStyle={{ padding: 0 }}>
          <ErrorState
            status="warning"
            fullHeight={false}
            title="Не удалось загрузить категории"
            description={getErrorMessage(categoriesErrorObj)}
            onRetry={() => refetchCategories()}
            retryLabel="Повторить попытку"
          />
        </Card>
      )}

      <BudgetVersionDetailDrawer
        open={isVersionDetailOpen}
        mode={versionDetailMode}
        versionId={activeVersionId}
        categories={categoryOptions}
        onClose={handleVersionDrawerClose}
        onVersionUpdated={refetchVersions}
      />
    </div>
  )
}

export default BudgetPlanningPage
