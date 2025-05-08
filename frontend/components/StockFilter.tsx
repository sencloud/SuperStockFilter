'use client'

import React, { useState, useEffect } from 'react'
import {
  Card,
  Form,
  Select,
  Button,
  Space,
  Table,
  Tag,
  Row,
  Col,
  Tabs,
  Radio,
  Statistic,
  Descriptions,
  Spin,
  Typography,
  Input,
  Divider,
  Tooltip,
  Badge,
  Modal,
  message,
} from 'antd'
import {
  LineChartOutlined,
  FilterOutlined,
  SearchOutlined,
  ReloadOutlined,
  SaveOutlined,
  BarChartOutlined,
  RiseOutlined,
  FallOutlined,
  DownloadOutlined,
} from '@ant-design/icons'
import type { ColumnsType } from 'antd/es/table'
import ReactMarkdown from 'react-markdown'
import { API_BASE_URL } from '../config'
import StockDetail from './StockDetail'

const { Title, Text } = Typography

export interface StockData {
  ts_code: string
  name: string
  industry: string
  market: string
  area: string
  list_date: string
  price: number
  change: number
  volume: number
  amount: number
  pe: number
  pb: number
  total_mv: number
}

interface FilterData {
  marketTypes: string[]
  industries: string[]
  indexComponents: Array<[string, string]>  // [code, name] tuples
}

const columns: ColumnsType<StockData> = [
  {
    title: '股票代码',
    dataIndex: 'ts_code',
    key: 'ts_code',
    fixed: 'left',
    width: 100,
    render: (text) => <a>{text}</a>,
  },
  {
    title: '股票名称',
    dataIndex: 'name',
    key: 'name',
    fixed: 'left',
    width: 100,
  },
  {
    title: '最新价',
    dataIndex: 'price',
    key: 'price',
    width: 90,
    align: 'right',
    sorter: (a, b) => (a.price || 0) - (b.price || 0),
    render: (text, record) => (
      <Text strong type={(record.change || 0) >= 0 ? 'danger' : 'success'}>
        {text ? text.toFixed(2) : '-'}
      </Text>
    ),
  },
  {
    title: '涨跌幅',
    dataIndex: 'change',
    key: 'change',
    width: 90,
    align: 'right',
    sorter: (a, b) => (a.change || 0) - (b.change || 0),
    render: (text) => (
      <Space>
        {(text || 0) >= 0 ? <RiseOutlined style={{ color: '#cf1322' }} /> : <FallOutlined style={{ color: '#52c41a' }} />}
        <Text type={(text || 0) >= 0 ? 'danger' : 'success'}>{text ? Math.abs(text).toFixed(2) : '-'}%</Text>
      </Space>
    ),
  },
  {
    title: '成交量(万手)',
    dataIndex: 'volume',
    key: 'volume',
    width: 110,
    align: 'right',
    sorter: (a, b) => (a.volume || 0) - (b.volume || 0),
    render: (text) => text ? (text / 10000).toFixed(2) : '-',
  },
  {
    title: '成交额(万元)',
    dataIndex: 'amount',
    key: 'amount',
    width: 120,
    align: 'right',
    sorter: (a, b) => (a.amount || 0) - (b.amount || 0),
    render: (text) => text ? (text / 10).toFixed(2) : '-',
  },
  {
    title: '市盈率',
    dataIndex: 'pe',
    key: 'pe',
    width: 90,
    align: 'right',
    sorter: (a, b) => (a.pe || 0) - (b.pe || 0),
    render: (text) => text ? text.toFixed(2) : '-',
  },
  {
    title: '市净率',
    dataIndex: 'pb',
    key: 'pb',
    width: 90,
    align: 'right',
    sorter: (a, b) => (a.pb || 0) - (b.pb || 0),
    render: (text) => text ? text.toFixed(2) : '-',
  },
  {
    title: '总市值(亿)',
    dataIndex: 'total_mv',
    key: 'total_mv',
    width: 110,
    align: 'right',
    sorter: (a, b) => (a.total_mv || 0) - (b.total_mv || 0),
    render: (text) => text ? (text / 10000).toFixed(2) : '-',
  },
  {
    title: '所属行业',
    dataIndex: 'industry',
    key: 'industry',
    width: 120,
    render: (text) => <Tag color="blue">{text}</Tag>,
  },
  {
    title: '市场',
    dataIndex: 'market',
    key: 'market',
    width: 100,
    render: (text) => <Tag color="green">{text}</Tag>,
  },
]

export default function StockFilter() {
  const [form] = Form.useForm()
  const [selectedStock, setSelectedStock] = useState<StockData | null>(null)
  const [isAnalyzing, setIsAnalyzing] = useState(false)
  const [showDetail, setShowDetail] = useState(false)
  const [loading, setLoading] = useState(false)
  const [filterData, setFilterData] = useState<FilterData>({
    marketTypes: [],
    industries: [],
    indexComponents: []
  })
  const [stockList, setStockList] = useState<StockData[]>([])
  const [pagination, setPagination] = useState({
    current: 1,
    pageSize: 20,
    total: 0
  })
  const [analysis, setAnalysis] = useState<string>('')
  const [currentTime, setCurrentTime] = useState('')

  useEffect(() => {
    setCurrentTime(new Date().toLocaleString())
    const timer = setInterval(() => {
      setCurrentTime(new Date().toLocaleString())
    }, 1000)
    return () => clearInterval(timer)
  }, [])

  // 计算统计数据
  const calculateStats = () => {
    if (!stockList || stockList.length === 0) {
      return {
        avgChange: 0,
        avgAmount: 0
      }
    }

    const validStocks = stockList.filter(stock => stock.change != null && stock.amount != null)
    if (validStocks.length === 0) {
      return {
        avgChange: 0,
        avgAmount: 0
      }
    }

    const totalChange = validStocks.reduce((sum, stock) => sum + (stock.change || 0), 0)
    const totalAmount = validStocks.reduce((sum, stock) => sum + (stock.amount || 0), 0)

    return {
      avgChange: totalChange / validStocks.length,
      avgAmount: totalAmount / validStocks.length / 10 // 转换为万元
    }
  }

  // 获取筛选数据
  useEffect(() => {
    const fetchFilterData = async () => {
      try {
        const [marketTypesRes, industriesRes, indexComponentsRes] = await Promise.all([
          fetch(`${API_BASE_URL}/market-types`),
          fetch(`${API_BASE_URL}/industries`),
          fetch(`${API_BASE_URL}/index-components`),
        ])

        const marketTypes = await marketTypesRes.json()
        const industries = await industriesRes.json()
        const indexComponents = await indexComponentsRes.json()

        setFilterData({
          marketTypes: marketTypes.data || [],
          industries: industries.data || [],
          indexComponents: indexComponents.data || [],
        })
      } catch (error) {
        message.error('获取筛选数据失败')
        console.error('获取筛选数据失败:', error)
      }
    }

    fetchFilterData()
  }, [])

  const handleFilter = async (values: any) => {
    setLoading(true)
    try {
      const response = await fetch(`${API_BASE_URL}/filter`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          market_types: values.market_types,
          industries: values.industries,
          index_components: values.index_components,
          kline_pattern: values.kline_pattern,
          price_prediction: values.price_prediction,
          page: 1,
          page_size: pagination.pageSize
        }),
      })

      const result = await response.json()
      setStockList(result.data)
      setPagination(prev => ({
        ...prev,
        current: 1,
        total: result.total
      }))
    } catch (error) {
      message.error('筛选失败')
      console.error('筛选失败:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleTableChange = async (newPagination: any) => {
    setLoading(true)
    try {
      const values = form.getFieldsValue()
      const response = await fetch(`${API_BASE_URL}/filter`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          market_types: values.market_types,
          industries: values.industries,
          index_components: values.index_components,
          kline_pattern: values.kline_pattern,
          price_prediction: values.price_prediction,
          page: newPagination.current,
          page_size: newPagination.pageSize
        }),
      })

      const result = await response.json()
      if (result.data) {
        setStockList(result.data)
        setPagination({
          current: newPagination.current,
          pageSize: newPagination.pageSize,
          total: result.total
        })
      }
    } catch (error) {
      message.error('获取数据失败')
      console.error('获取数据失败:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleAnalyze = async () => {
    if (!selectedStock) return
    setIsAnalyzing(true)
    try {
      const response = await fetch(`${API_BASE_URL}/stock/${selectedStock.ts_code}/analysis`)
      const result = await response.json()
      setAnalysis(result.data)
    } catch (error) {
      message.error('分析失败')
      console.error('分析失败:', error)
    } finally {
      setIsAnalyzing(false)
    }
  }

  const handleStockSelect = async (stock: StockData) => {
    setSelectedStock(stock)
    setShowDetail(true)
    try {
      const response = await fetch(`${API_BASE_URL}/stock/${stock.ts_code}`)
      const result = await response.json()
      setSelectedStock({ ...stock, ...result.data })
    } catch (error) {
      message.error('获取股票详情失败')
      console.error('获取股票详情失败:', error)
    }
  }

  const handleExport = () => {
    if (!stockList.length) {
      message.warning('没有可导出的数据')
      return
    }

    // 准备CSV数据
    const headers = [
      '股票代码', '股票名称', '最新价', '涨跌幅', '成交量(万手)',
      '成交额(万元)', '市盈率', '市净率', '总市值(亿)', '所属行业', '市场'
    ]
    
    const csvContent = [
      headers.join(','),
      ...stockList.map(stock => [
        stock.ts_code,
        stock.name,
        stock.price?.toFixed(2) || '',
        stock.change?.toFixed(2) || '',
        stock.volume ? (stock.volume / 10000).toFixed(2) : '',
        stock.amount ? (stock.amount / 10).toFixed(2) : '',
        stock.pe?.toFixed(2) || '',
        stock.pb?.toFixed(2) || '',
        stock.total_mv ? (stock.total_mv / 10000).toFixed(2) : '',
        stock.industry,
        stock.market
      ].join(','))
    ].join('\n')

    // 创建Blob对象
    const blob = new Blob(['\ufeff' + csvContent], { type: 'text/csv;charset=utf-8;' })
    const url = URL.createObjectURL(blob)
    
    // 创建下载链接并触发下载
    const link = document.createElement('a')
    link.href = url
    link.download = `股票筛选结果_${new Date().toLocaleDateString()}.csv`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    URL.revokeObjectURL(url)
    
    message.success('导出成功')
  }

  return (
    <div style={{ display: 'flex', width: '100%', gap: 16 }}>
      <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: 16, minHeight: 0 }}>
        <Card>
          <Form
            form={form}
            name="stock_filter"
            onFinish={handleFilter}
            layout="vertical"
            initialValues={{
              kline_pattern: '所有',
              price_prediction: '所有',
            }}
          >
            <Row gutter={24}>
              <Col span={6}>
                <Form.Item name="keyword" label="股票代码/名称">
                  <Input
                    placeholder="输入代码或名称搜索"
                    prefix={<SearchOutlined />}
                    allowClear
                  />
                </Form.Item>
              </Col>
              <Col span={6}>
                <Form.Item name="market_types" label="市场类型">
                  <Select
                    mode="multiple"
                    placeholder="选择市场类型"
                    options={filterData.marketTypes.map(type => ({
                      value: type,
                      label: type,
                    }))}
                    maxTagCount="responsive"
                  />
                </Form.Item>
              </Col>
              <Col span={6}>
                <Form.Item name="industries" label="行业分类">
                  <Select
                    mode="multiple"
                    placeholder="选择行业"
                    options={filterData.industries.map(industry => ({
                      value: industry,
                      label: industry,
                    }))}
                    maxTagCount="responsive"
                  />
                </Form.Item>
              </Col>
              <Col span={6}>
                <Form.Item name="index_components" label="指数成分股">
                  <Select
                    mode="multiple"
                    placeholder="选择指数"
                    options={filterData.indexComponents.map(([code, name]) => ({
                      value: code,
                      label: name,
                    }))}
                    maxTagCount="responsive"
                  />
                </Form.Item>
              </Col>
            </Row>
            <Row gutter={24}>
              <Col span={8}>
                <Form.Item name="kline_pattern" label="K线形态">
                  <Select
                    placeholder="选择K线形态"
                    options={[
                      { value: '所有', label: '所有形态' },
                      { value: 'V型底', label: 'V型底' },
                      { value: 'W底', label: 'W底' },
                      { value: '启明之星', label: '启明之星' },
                      { value: '圆弧底', label: '圆弧底' },
                      { value: '头肩底', label: '头肩底' },
                      { value: '平底', label: '平底' },
                      { value: '旭日东升', label: '旭日东升' },
                      { value: '看涨吞没', label: '看涨吞没' },
                      { value: '红三兵', label: '红三兵' },
                      { value: '锤头线', label: '锤头线' },
                    ]}
                  />
                </Form.Item>
              </Col>
              <Col span={8}>
                <Form.Item name="price_prediction" label="价格预测">
                  <Select
                    placeholder="选择预测类型"
                    options={[
                      { value: '所有', label: '所有' },
                      { value: '涨停', label: '涨停' },
                      { value: '资金持续流入', label: '资金持续流入' },
                    ]}
                  />
                </Form.Item>
              </Col>
              <Col span={8} style={{ textAlign: 'right', marginTop: 30 }}>
                <Space>
                  <Button icon={<ReloadOutlined />} onClick={() => form.resetFields()}>
                    重置
                  </Button>
                  <Button icon={<DownloadOutlined />} onClick={handleExport}>
                    导出结果
                  </Button>
                  <Button type="primary" icon={<FilterOutlined />} htmlType="submit" loading={loading}>
                    开始筛选
                  </Button>
                </Space>
              </Col>
            </Row>
          </Form>
        </Card>

        <Card style={{ flex: 1, display: 'flex', flexDirection: 'column', minHeight: 0 }}>
          <Row gutter={16} style={{ marginBottom: 16 }}>
            <Col span={6}>
              <Statistic
                title="符合条件股票"
                value={pagination.total}
                suffix="只"
                prefix={<BarChartOutlined />}
              />
            </Col>
            <Col span={6}>
              <Statistic
                title="平均涨跌幅"
                value={calculateStats().avgChange}
                precision={2}
                prefix={<RiseOutlined />}
                suffix="%"
                valueStyle={{ color: calculateStats().avgChange >= 0 ? '#cf1322' : '#52c41a' }}
              />
            </Col>
            <Col span={6}>
              <Statistic
                title="平均成交额"
                value={calculateStats().avgAmount}
                precision={2}
                prefix={<LineChartOutlined />}
                suffix="万"
              />
            </Col>
            <Col span={6}>
              <Statistic
                title="最新更新时间"
                value={currentTime}
                prefix={<Badge status="processing" />}
              />
            </Col>
          </Row>

          <div style={{ flex: 1, minHeight: 0, overflow: 'auto' }}>
            <Table<StockData>
              columns={columns}
              dataSource={stockList}
              rowKey="ts_code"
              size="middle"
              scroll={{ x: 1300 }}
              loading={loading}
              pagination={{
                current: pagination.current,
                pageSize: pagination.pageSize,
                total: pagination.total,
                showSizeChanger: true,
                showQuickJumper: true,
                showTotal: (total) => `共 ${total} 条`
              }}
              onChange={(pagination, filters, sorter) => handleTableChange(pagination)}
              onRow={(record) => ({
                onClick: () => handleStockSelect(record),
              })}
            />
          </div>
        </Card>
      </div>
      <div style={{ width: 400 }}>
        <StockDetail stock={selectedStock} />
      </div>
    </div>
  )
} 