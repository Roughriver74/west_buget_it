# Интеграция индикатора прогресса синхронизации

## Что сделано

✅ Создан компонент `SyncProgressModal` в `/frontend/src/components/bank/SyncProgressModal.tsx`

## Что нужно добавить в BankTransactionsPage.tsx

### 1. Добавить импорт (после строки 46 - `import ColumnMappingModal...`):

```typescript
import SyncProgressModal from '@/components/bank/SyncProgressModal'
```

### 2. Добавить состояния (после строки ~85 - где объявляются модальные окна):

```typescript
  // Sync progress modal
  const [syncProgressModalOpen, setSyncProgressModalOpen] = useState(false)
  const [syncTaskId, setSyncTaskId] = useState<string | null>(null)
```

### 3. Заменить `odataSyncMutation` (строки 322-380):

```typescript
  // OData sync mutation (Background Task with Progress Modal)
  const odataSyncMutation = useMutation({
    mutationFn: (params: {
      odata_url: string
      username: string
      password: string
      entity_name?: string
      department_id: number
      organization_id?: number
      date_from?: string
      date_to?: string
    }) => bankTransactionsApi.syncFromOData(params),
    onSuccess: (result) => {
      // Закрываем форму синхронизации
      setOdataSyncModalOpen(false)
      odataSyncForm.resetFields()

      // Открываем модалку прогресса
      setSyncTaskId(result.task_id)
      setSyncProgressModalOpen(true)
    },
    onError: (error: any) => {
      message.error(`Ошибка запуска синхронизации: ${error.response?.data?.detail || error.message}`)
    },
  })
```

### 4. Добавить обработчик завершения синхронизации (после `odataSyncMutation`):

```typescript
  const handleSyncComplete = (success: boolean, result?: any) => {
    setSyncProgressModalOpen(false)
    setSyncTaskId(null)

    if (success && result) {
      message.success(
        `✅ Синхронизация завершена: создано ${result.created}, обновлено ${result.updated}`
      )
      queryClient.invalidateQueries({ queryKey: ['bankTransactions'] })
      queryClient.invalidateQueries({ queryKey: ['bankTransactionsStats'] })
    }
  }
```

### 5. Добавить компонент в JSX (перед закрывающим `</div>` в конце файла, строка ~1494):

```typescript
      {/* Sync Progress Modal */}
      <SyncProgressModal
        open={syncProgressModalOpen}
        taskId={syncTaskId}
        onComplete={handleSyncComplete}
        onCancel={() => {
          setSyncProgressModalOpen(false)
          setSyncTaskId(null)
        }}
      />
    </div>
  )
}
```

### 6. Исправить пагинацию таблицы (найти `<Table` компонент, добавить `pagination`):

Найти строку где рендерится `<Table` (примерно строка ~1165) и добавить:

```typescript
          <Table<BankTransaction>
            className="bank-transactions-table"
            dataSource={data?.items || []}
            columns={columns}
            rowKey="id"
            loading={isLoading}
            size="small"
            scroll={{ x: 1800 }}
            pagination={{
              current: page,
              pageSize,
              total: data?.total || 0,
              showTotal: (total, range) => `${range[0]}-${range[1]} из ${total} записей`,
              showSizeChanger: true,
              pageSizeOptions: ['20', '50', '100', '200'],
              onChange: (newPage, newPageSize) => {
                setPage(newPage)
                if (newPageSize !== pageSize) {
                  setPageSize(newPageSize)
                  setPage(1) // Reset to first page when page size changes
                }
              },
            }}
            // ... rest of props
```

## Результат

После этих изменений:

✅ **Индикатор загрузки** - во время синхронизации показывается модальное окно с прогресс-баром
✅ **Статус в реальном времени** - обновления каждые 5 секунд
✅ **Результат синхронизации** - красивое отображение итогов (создано/обновлено/пропущено)
✅ **Правильная пагинация** - пользователь видит все записи через переключатель страниц
✅ **Настройка количества записей** - 20/50/100/200 на странице

## Тестирование

1. Перейти на страницу "Банковские транзакции"
2. Нажать "Синхронизировать с 1С"
3. Выбрать период (например, 17.11.2025 - 17.11.2025)
4. Нажать "Синхронизировать"
5. **Увидеть модальное окно с прогрессом**
6. После завершения увидеть результат
7. **Переключить страницы** внизу таблицы, чтобы увидеть все записи
