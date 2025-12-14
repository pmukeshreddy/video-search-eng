import './globals.css'

export const metadata = {
  title: 'Semantic Video Search',
  description: 'Search video content with natural language using CLIP',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  )
}
