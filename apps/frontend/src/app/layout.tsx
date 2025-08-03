import './globals.css'
import { Inter } from 'next/font/google'
import { Providers } from './providers'
import { Toaster } from 'react-hot-toast'

const inter = Inter({ subsets: ['latin'] })

export const metadata = {
  title: 'Tramites AI Perú - Asistente Virtual para Trámites Gubernamentales',
  description: 'Simplifica tus trámites gubernamentales en Perú con nuestro asistente de inteligencia artificial. Obtén información clara, genera documentos y completa tus gestiones más rápido.',
  keywords: 'trámites, perú, gobierno, IA, asistente virtual, documentos, SUNAT, RENIEC, municipalidad',
  authors: [{ name: 'Tramites AI Perú' }],
  creator: 'Tramites AI Perú',
  publisher: 'Tramites AI Perú',
  formatDetection: {
    email: false,
    address: false,
    telephone: false,
  },
  openGraph: {
    title: 'Tramites AI Perú - Asistente Virtual para Trámites',
    description: 'Simplifica tus trámites gubernamentales con inteligencia artificial',
    url: 'https://tramites-ai.pe',
    siteName: 'Tramites AI Perú',
    images: [
      {
        url: '/og-image.png',
        width: 1200,
        height: 630,
        alt: 'Tramites AI Perú',
      },
    ],
    locale: 'es_PE',
    type: 'website',
  },
  twitter: {
    card: 'summary_large_image',
    title: 'Tramites AI Perú - Asistente Virtual para Trámites',
    description: 'Simplifica tus trámites gubernamentales con inteligencia artificial',
    images: ['/og-image.png'],
    creator: '@tramitesaiperu',
  },
  robots: {
    index: true,
    follow: true,
    googleBot: {
      index: true,
      follow: true,
      'max-video-preview': -1,
      'max-image-preview': 'large',
      'max-snippet': -1,
    },
  },
  icons: {
    icon: '/favicon.ico',
    shortcut: '/favicon-16x16.png',
    apple: '/apple-touch-icon.png',
  },
  manifest: '/site.webmanifest',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="es" className="h-full">
      <body className={`${inter.className} h-full`}>
        <Providers>
          {children}
          <Toaster
            position="top-right"
            toastOptions={{
              duration: 4000,
              style: {
                background: '#363636',
                color: '#fff',
              },
              success: {
                iconTheme: {
                  primary: '#10b981',
                  secondary: '#fff',
                },
              },
              error: {
                iconTheme: {
                  primary: '#ef4444',
                  secondary: '#fff',
                },
              },
            }}
          />
        </Providers>
      </body>
    </html>
  )
}
