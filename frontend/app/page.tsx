'use client'

import React from 'react'
import { Layout, Menu, theme, Typography } from 'antd'
import {
  DashboardOutlined,
  FundOutlined,
  SettingOutlined,
  FilterOutlined,
} from '@ant-design/icons'
import StockFilter from '@/components/StockFilter'

const { Header, Content, Sider } = Layout
const { Title } = Typography

export default function Home() {
  const {
    token: { colorBgContainer, borderRadiusLG },
  } = theme.useToken()

  return (
    <Layout style={{ height: '100vh' }}>
      <Header style={{ 
        background: colorBgContainer, 
        padding: '0 16px', 
        display: 'flex', 
        alignItems: 'center',
        position: 'fixed',
        width: '100%',
        top: 0,
        zIndex: 1,
        borderBottom: '1px solid #f0f0f0',
        height: 64
      }}>
        <Title level={3} style={{ margin: 0, color: '#000000' }}>
          超级股票过滤器
        </Title>
      </Header>
      <Layout>
        <Sider 
          width={200} 
          style={{ 
            background: colorBgContainer,
            position: 'fixed',
            left: 0,
            top: 64,
            bottom: 0,
            zIndex: 1,
            borderRight: '1px solid #f0f0f0'
          }}
        >
          <Menu
            mode="inline"
            defaultSelectedKeys={['1']}
            style={{ height: '100%', borderRight: 0 }}
            items={[
              {
                key: '1',
                icon: <FilterOutlined />,
                label: '选股器',
              },
              {
                key: '2',
                icon: <FundOutlined />,
                label: '市场概览',
              },
              {
                key: '3',
                icon: <DashboardOutlined />,
                label: '量化分析',
              },
              {
                key: '4',
                icon: <SettingOutlined />,
                label: '系统设置',
              },
            ]}
          />
        </Sider>
        <Layout style={{ marginLeft: 200, marginTop: 64 }}>
          <Content
            style={{
              padding: 24,
              background: colorBgContainer,
              borderRadius: borderRadiusLG,
              minHeight: 'calc(100vh - 64px)',
              display: 'flex'
            }}
          >
            <StockFilter />
          </Content>
        </Layout>
      </Layout>
    </Layout>
  )
} 