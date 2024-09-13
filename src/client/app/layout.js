import localFont from "next/font/local"
import './main.css'

const geistSans = localFont({
    src: "../../lib/assets/fonts/GeistVF.woff",
    variable: "--font-geist-sans",
    weight: "100 900",
})

const geistMono = localFont({
    src: "../../lib/assets/fonts/GeistMonoVF.woff",
    variable: "--font-geist-mono",
    weight: "100 900",
})

export const metadata = {
    title: "EcomGo",
    description: "AI-Powered E-commerce App",
};

export default function RootLayout({ children }) {
  return (
      <html lang="en">
        <body className={`${geistSans.variable} ${geistMono.variable}`}>
          {children}
        </body>
      </html>
  )
}
