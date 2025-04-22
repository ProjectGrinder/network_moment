import React, { createContext, useContext, useEffect } from 'react'
import { socketManager, WebSocketManager } from '@/api/api'

export function useWebSocketEvent<T = any>(
  eventType: string,
  callback: (payload: T) => void,
) {
  const ws = useContext(WebSocketContext)

  useEffect(() => {
    if (!ws) return

    ws.subscribe<T>(eventType, callback)
    return () => {
      ws.unsubscribe<T>(eventType, callback)
    }
  }, [ws, eventType, callback])
}

export const WebSocketContext = createContext<WebSocketManager | null>(null)

export const WebSocketProvider: React.FC<{
  children: React.ReactNode
  location: string
}> = ({ children, location }) => {
  useEffect(() => {
    socketManager.connect(location)
    return () => {
      console.log('this called')
      socketManager.disconnect()
    }
  }, [])

  return (
    <WebSocketContext.Provider value={socketManager}>
      {children}
    </WebSocketContext.Provider>
  )
}
