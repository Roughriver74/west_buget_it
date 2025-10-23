import { useState } from 'react'
import { Layout, Menu, theme } from 'antd'
import { Link, useLocation } from 'react-router-dom'
import {
  DashboardOutlined,
  FileTextOutlined,
  DollarOutlined,
  DatabaseOutlined,
  BarChartOutlined,
} from '@ant-design/icons'

const { Header, Content, Sider } = Layout

interface AppLayoutProps {
  children: React.ReactNode
}

const AppLayout: React.FC<AppLayoutProps> = ({ children }) => {
  const [collapsed, setCollapsed] = useState(false)
  const location = useLocation()
  const {
    token: { colorBgContainer, borderRadiusLG },
  } = theme.useToken()

  const menuItems = [
    {
      key: '/dashboard',
      icon: <DashboardOutlined />,
      label: <Link to="/dashboard">Дашборд</Link>,
    },
    {
      key: '/expenses',
      icon: <FileTextOutlined />,
      label: <Link to="/expenses">Заявки</Link>,
    },
    {
      key: '/budget',
      icon: <DollarOutlined />,
      label: <Link to="/budget">Бюджет</Link>,
    },
    {
      key: '/analytics',
      icon: <BarChartOutlined />,
      label: <Link to="/analytics">Аналитика</Link>,
    },
    {
      key: '/references',
      icon: <DatabaseOutlined />,
      label: <Link to="/references">Справочники</Link>,
    },
  ]

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Sider collapsible collapsed={collapsed} onCollapse={(value) => setCollapsed(value)}>
        <div
          style={{
            height: 32,
            margin: 16,
            color: 'white',
            fontSize: collapsed ? 14 : 18,
            fontWeight: 'bold',
            textAlign: 'center',
          }}
        >
          {collapsed ? 'ITB' : 'IT Budget'}
        </div>
        <Menu
          theme="dark"
          selectedKeys={[location.pathname]}
          mode="inline"
          items={menuItems}
        />
      </Sider>
      <Layout>
        <Header style={{ padding: 0, background: colorBgContainer }}>
          <div style={{ padding: '0 24px', fontSize: 20, fontWeight: 500 }}>
            IT Budget Manager
          </div>
        </Header>
        <Content style={{ margin: '24px 16px 0' }}>
          <div
            style={{
              padding: 24,
              minHeight: 360,
              background: colorBgContainer,
              borderRadius: borderRadiusLG,
            }}
          >
            {children}
          </div>
        </Content>
      </Layout>
    </Layout>
  )
}

export default AppLayout
