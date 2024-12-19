import { Metadata, ParentProps } from '@/helpers/interfaces'
import { AppProvider } from '@/helpers/context'
import './main.css'

export const metadata: Metadata = { title: "EcomGo", description: "AI-Powered E-commerce App" }
export default function RootLayout({ children }: ParentProps) {
    return (
        <html lang='en'>
            <head>
                <link rel='icon' href='favicon.ico' />
            </head>
            <body>
                <AppProvider>{children}</AppProvider>
            </body>
        </html>
    )
}