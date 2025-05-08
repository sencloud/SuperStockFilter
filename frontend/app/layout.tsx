import { Inter } from 'next/font/google'
import StyledComponentsRegistry from '@/lib/AntdRegistry'
import { ConfigProvider } from 'antd'
import zhCN from 'antd/locale/zh_CN'
import theme from '@/theme/themeConfig'

const inter = Inter({ subsets: ['latin'] })

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="zh">
      <body className={inter.className}>
        <StyledComponentsRegistry>
          <ConfigProvider
            theme={theme}
            locale={zhCN}
          >
            {children}
          </ConfigProvider>
        </StyledComponentsRegistry>
      </body>
    </html>
  )
} 