import React, { useState } from 'react'
import {
  Descriptions,
  Typography,
  Button,
  Spin,
  Divider,
  Space,
  Tag,
  Empty
} from 'antd'
import { LineChartOutlined } from '@ant-design/icons'
import ReactMarkdown from 'react-markdown'
import type { StockData } from './StockFilter'
import * as echarts from 'echarts'
import { API_BASE_URL } from '../config'

const { Text } = Typography

interface StockDetailProps {
  stock: StockData | null
  width?: number
}

const StockDetail: React.FC<StockDetailProps> = ({ stock, width = 400 }) => {
  const [isAnalyzing, setIsAnalyzing] = useState(false)
  const [analysis, setAnalysis] = useState<string>('')
  const chartRef = React.useRef<HTMLDivElement>(null)
  const chartInstanceRef = React.useRef<echarts.ECharts | null>(null)
  const [klineData, setKlineData] = useState<any[]>([])
  const [isLoadingKline, setIsLoadingKline] = useState(false)

  const handleAnalyze = async () => {
    if (!stock) return
    setIsAnalyzing(true)
    try {
      const response = await fetch(`${API_BASE_URL}/stock/${stock.ts_code}/analysis`)
      const result = await response.json()
      setAnalysis(result.data)
    } catch (error) {
      console.error('分析失败:', error)
    } finally {
      setIsAnalyzing(false)
    }
  }

  const fetchKlineData = async () => {
    if (!stock) return
    setIsLoadingKline(true)
    try {
      const response = await fetch(`${API_BASE_URL}/stock/${stock.ts_code}/kline`)
      const data = await response.json()
      setKlineData(data.data)
    } catch (error) {
      console.error('获取K线数据失败:', error)
    } finally {
      setIsLoadingKline(false)
    }
  }

  const initChart = () => {
    if (!chartRef.current || !klineData.length) return

    // 清理旧的图表实例
    if (chartInstanceRef.current) {
      chartInstanceRef.current.dispose()
    }

    // 创建新的图表实例
    const chart = echarts.init(chartRef.current)
    chartInstanceRef.current = chart

    const option = {
      tooltip: {
        trigger: 'axis',
        axisPointer: {
          type: 'cross'
        }
      },
      grid: {
        left: '10%',
        right: '10%',
        bottom: '15%'
      },
      xAxis: {
        type: 'category',
        data: klineData.map(item => item.trade_date),
        scale: true
      },
      yAxis: {
        type: 'value',
        scale: true
      },
      series: [
        {
          name: '日K',
          type: 'candlestick',
          data: klineData.map(item => [
            item.open,
            item.close,
            item.low,
            item.high
          ])
        }
      ]
    }

    chart.setOption(option)
  }

  React.useEffect(() => {
    if (stock) {
      fetchKlineData()
      setAnalysis('') // 重置分析结果
    }
    
    // 组件卸载时清理图表实例
    return () => {
      if (chartInstanceRef.current) {
        chartInstanceRef.current.dispose()
        chartInstanceRef.current = null
      }
    }
  }, [stock?.ts_code])

  // 监听klineData变化，更新图表
  React.useEffect(() => {
    if (klineData.length > 0) {
      initChart()
    }
  }, [klineData])

  // 监听窗口大小变化，调整图表大小
  React.useEffect(() => {
    const handleResize = () => {
      if (chartInstanceRef.current) {
        chartInstanceRef.current.resize()
      }
    }

    window.addEventListener('resize', handleResize)
    return () => window.removeEventListener('resize', handleResize)
  }, [])

  if (!stock) {
    return (
      <div style={{ width, padding: '24px', textAlign: 'center' }}>
        <Empty description="请选择股票查看详情" />
      </div>
    )
  }

  return (
    <div style={{ width, padding: '24px', borderLeft: '1px solid #f0f0f0' }}>
      <Space>
        <span>{stock.name}</span>
        <Tag color="blue">{stock.ts_code}</Tag>
      </Space>

      <Divider />

      <div style={{ height: '300px', marginBottom: '24px' }} ref={chartRef}>
        {isLoadingKline && <Spin />}
      </div>

      <Descriptions bordered column={1} size="small">
        <Descriptions.Item label="最新价">
          <Text strong type={stock.change >= 0 ? 'danger' : 'success'}>
            {stock.price?.toFixed(2)}
          </Text>
        </Descriptions.Item>
        <Descriptions.Item label="涨跌幅">
          <Text type={stock.change >= 0 ? 'danger' : 'success'}>
            {stock.change?.toFixed(2)}%
          </Text>
        </Descriptions.Item>
        <Descriptions.Item label="成交量">{(stock.volume / 10000)?.toFixed(2)}万手</Descriptions.Item>
        <Descriptions.Item label="成交额">{(stock.amount / 10000)?.toFixed(2)}万元</Descriptions.Item>
        <Descriptions.Item label="市盈率">{stock.pe?.toFixed(2)}</Descriptions.Item>
        <Descriptions.Item label="市净率">{stock.pb?.toFixed(2)}</Descriptions.Item>
        <Descriptions.Item label="总市值">{(stock.total_mv / 100000000)?.toFixed(2)}亿</Descriptions.Item>
        <Descriptions.Item label="上市日期">{stock.list_date}</Descriptions.Item>
        <Descriptions.Item label="所属行业">{stock.industry}</Descriptions.Item>
        <Descriptions.Item label="地区">{stock.area}</Descriptions.Item>
      </Descriptions>

      <Divider />

      <div>
        {isAnalyzing ? (
          <Spin tip="正在进行深度分析..." />
        ) : analysis ? (
          <div style={{ textAlign: 'left', padding: '16px' }}>
            <ReactMarkdown>{analysis}</ReactMarkdown>
          </div>
        ) : (
          <Button type="primary" onClick={handleAnalyze} icon={<LineChartOutlined />}>
            DeepSeek分析
          </Button>
        )}
      </div>
    </div>
  )
}

export default StockDetail 